"""The local HTTP API used by the web app. It listens on 127.0.0.1 only.

    GET  /api/health                         what is ready (language model, voice)
    GET  /api/catalog                        the algorithms the pipeline can explain
    GET  /api/plans, /api/plans/{id}         saved, verified lesson plans
    POST /api/plans/{id}/render              make a video from a saved plan (no API key needed)
    POST /api/lessons                        make a new lesson from a topic
    GET  /api/lessons, /api/lessons/{id}     lessons made on this machine
    DELETE /api/lessons/{id}
    POST /api/lessons/{id}/revisions         "slow down step 4", "explain step 2 for a beginner"
    GET  /api/lessons/{id}/videos/{version}  the video (supports seeking)
    GET  /api/clips/{key}                    one finished clip, playable before the whole video is joined
    GET  /api/jobs, /api/jobs/{id}           job state
    GET  /api/jobs/{id}/events               Server-Sent Events: the job's progress, replayed then live
    POST /api/jobs/{id}/cancel
    GET/PUT /api/settings                    preferences
"""

from __future__ import annotations

import asyncio
import json
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from .. import config, pipeline, settings, store
from ..core.lesson import Lesson, scene_labels
from ..core.structures import DISPLAY_NAMES, STRUCTURES
from ..core.verifier import answer_index, verify_lesson
from .jobs import JobManager, JobReporter

Quality = Literal["draft", "standard", "high"]
LevelName = Literal["beginner", "intermediate", "advanced"]


class CreateLesson(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    level: LevelName = "beginner"
    quality: Quality | None = None


class RenderPlan(BaseModel):
    quality: Quality | None = None


class Revise(BaseModel):
    request: str = Field(min_length=2, max_length=500)
    version: int | None = None
    quality: Quality | None = None


# --- helpers --------------------------------------------------------------------------


def _quality(q: str | None) -> str:
    return q or config.DEFAULT_QUALITY


def _plan_files() -> dict[str, object]:
    return {p.stem: p for p in sorted(config.PLANS_DIR.glob("*.json"))}


def plan_summary(plan_id: str, lesson: Lesson) -> dict:
    steps = sum(s.kind == "step" for s in lesson.scenes)
    return {"id": plan_id, "title": lesson.title, "topic": lesson.topic, "structure": lesson.structure,
            "level": lesson.level, "steps": steps, "questions": len(lesson.quiz)}


def lesson_view(lesson: Lesson) -> dict:
    """The parts of a verified lesson the page shows: scenes, quiz with checked answers, verification."""
    report = verify_lesson(lesson)
    scenes = [{"label": label, "kind": s.kind, "caption": s.caption, "narration": s.narration,
               "op": s.op.describe() if s.op else None, "speed": s.speed, "points": s.points}
              for label, s in zip(scene_labels(lesson), lesson.scenes)]
    quiz = []
    for q in lesson.quiz:
        try:
            right = answer_index(lesson, q)
        except Exception:  # an unverifiable question is never shown
            continue
        quiz.append({"question": q.question, "options": q.options, "answer": right, "explanation": q.explanation})
    return {"scenes": scenes, "quiz": quiz,
            "verified": {"ok": report.ok, "checks": report.checks, "errors": report.errors[:5]},
            "plan": lesson.model_dump(mode="json")}


def _not_found(exc: Exception):
    raise HTTPException(status_code=404, detail=str(exc)) from exc


# --- the app --------------------------------------------------------------------------


def create_app() -> FastAPI:
    settings.apply()
    app = FastAPI(title="DSA Explainer", version=config.VERSION, docs_url="/api/docs", openapi_url="/api/openapi.json")
    jobs = JobManager()
    app.state.jobs = jobs

    @app.exception_handler(store.NotFound)
    async def not_found(_: Request, exc: store.NotFound):
        return JSONResponse({"detail": str(exc)}, status_code=404)

    @app.exception_handler(settings.SettingsError)
    async def bad_setting(_: Request, exc: settings.SettingsError):
        return JSONResponse({"detail": str(exc)}, status_code=400)

    # --- status and catalogue ---

    @app.get("/api/health")
    def health():
        return {
            "ok": True, "version": config.VERSION,
            "llm": {"configured": bool(config.LLM_API_KEY), "model": config.LLM_MODEL,
                    "base_url": config.LLM_BASE_URL},
            "voice": {"ready": config.KOKORO_MODEL.exists() and config.KOKORO_VOICES.exists(),
                      "voice": config.KOKORO_VOICE},
            "busy": any(j.status == "running" for j in jobs.list()),
        }

    @app.get("/api/catalog")
    def catalog():
        return [{"id": name, "name": DISPLAY_NAMES.get(name, name), "operations": list(cls.OPS),
                 "facts": list(cls.FACTS), "help": cls.HELP} for name, cls in STRUCTURES.items()]

    # --- saved plans ---

    @app.get("/api/plans")
    def plans():
        out = []
        for plan_id, path in _plan_files().items():
            out.append(plan_summary(plan_id, Lesson.model_validate_json(path.read_text(encoding="utf-8"))))
        return out

    @app.get("/api/plans/{plan_id}")
    def plan(plan_id: str):
        path = _plan_files().get(plan_id)
        if path is None:
            raise HTTPException(404, f"no saved plan '{plan_id}'")
        lesson = Lesson.model_validate_json(path.read_text(encoding="utf-8"))
        return {**plan_summary(plan_id, lesson), **lesson_view(lesson)}

    @app.post("/api/plans/{plan_id}/render", status_code=202)
    def render_plan(plan_id: str, body: RenderPlan | None = None):
        path = _plan_files().get(plan_id)
        if path is None:
            raise HTTPException(404, f"no saved plan '{plan_id}'")
        quality = _quality(body.quality if body else None)

        def run(rep: JobReporter) -> dict:
            result = pipeline.from_file(path, quality, rep)
            return {"lesson_id": result["lesson_id"], "version": result["version"]}

        return jobs.submit("render", {"plan": plan_id, "quality": quality}, run).snapshot()

    # --- lessons ---

    @app.post("/api/lessons", status_code=202)
    def create_lesson(body: CreateLesson):
        if not config.LLM_API_KEY:
            raise HTTPException(400, "No language model is set up. Add an API key in Settings, or watch a saved lesson.")
        quality = _quality(body.quality)

        def run(rep: JobReporter) -> dict:
            result = pipeline.make_lesson(body.topic, body.level, quality, rep)
            return {"lesson_id": result["lesson_id"], "version": result["version"]}

        return jobs.submit("create", {"topic": body.topic, "level": body.level, "quality": quality}, run).snapshot()

    @app.get("/api/lessons")
    def lessons():
        return store.list_lessons()

    @app.get("/api/lessons/{lesson_id}")
    def lesson(lesson_id: str, version: int | None = None):
        meta, _ = store.get(lesson_id)
        versions = meta.get("versions", [])
        if version is None:
            version = versions[-1]["version"] if versions else 1
        info = next((v for v in versions if v.get("version") == version), None)
        if info is None:
            raise HTTPException(404, f"lesson '{lesson_id}' has no version {version}")
        view = lesson_view(store.lesson(lesson_id, version))
        return {**meta, "version": version, "version_info": info,
                "video_url": f"/api/lessons/{lesson_id}/videos/{version}", **view}

    @app.delete("/api/lessons/{lesson_id}", status_code=204)
    def delete_lesson(lesson_id: str):
        store.delete(lesson_id)

    @app.post("/api/lessons/{lesson_id}/revisions", status_code=202)
    def revise_lesson(lesson_id: str, body: Revise):
        meta, path = store.get(lesson_id)
        if not config.LLM_API_KEY and not pipeline.revise.is_rule_based(body.request):
            raise HTTPException(400, "Rewriting needs a language model. Speed changes ('slow down step 2') work "
                                     "without one.")
        latest = meta["versions"][-1]["version"] if meta.get("versions") else 1
        version = body.version or latest
        quality = _quality(body.quality)

        def run(rep: JobReporter) -> dict:
            result = pipeline.revise_lesson(path, version, body.request, quality, rep)
            return {"lesson_id": lesson_id, "version": result["version"], "changed": result.get("changed", [])}

        params = {"lesson_id": lesson_id, "request": body.request, "version": version, "quality": quality}
        return jobs.submit("revise", params, run).snapshot()

    @app.get("/api/lessons/{lesson_id}/videos/{version}")
    def video(lesson_id: str, version: int):
        return FileResponse(store.video(lesson_id, version), media_type="video/mp4")

    @app.get("/api/clips/{key}")
    def clip(key: str):
        return FileResponse(store.clip(key), media_type="video/mp4")

    # --- jobs ---

    @app.get("/api/jobs")
    def list_jobs():
        return [j.snapshot() for j in jobs.list()]

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str):
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(404, f"no job '{job_id}'")
        return job.snapshot(with_events=True)

    @app.post("/api/jobs/{job_id}/cancel")
    def cancel_job(job_id: str):
        job = jobs.cancel(job_id)
        if job is None:
            raise HTTPException(404, f"no job '{job_id}'")
        return job.snapshot()

    @app.get("/api/jobs/{job_id}/events")
    async def job_events(job_id: str, request: Request, after: int = -1):
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(404, f"no job '{job_id}'")
        last = request.headers.get("last-event-id")
        start = int(last) + 1 if last and last.isdigit() else after + 1

        async def stream():
            seq, idle = start, 0.0
            yield "retry: 2000\n\n"
            while True:
                fresh = job.events_since(seq)
                for event in fresh:
                    yield f"id: {event['seq']}\nevent: {event['type']}\ndata: {json.dumps(event)}\n\n"
                    seq = event["seq"] + 1
                if not fresh and job.finished_state:
                    yield f"event: end\ndata: {json.dumps(job.snapshot())}\n\n"
                    return
                if await request.is_disconnected():
                    return
                idle = 0.0 if fresh else idle + 0.25
                if idle >= 15:  # a comment keeps proxies and the browser from closing the stream
                    yield ": keep-alive\n\n"
                    idle = 0.0
                await asyncio.sleep(0.25)

        return StreamingResponse(stream(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    # --- settings ---

    @app.get("/api/settings")
    def get_settings():
        return {"preferences": settings.preferences(), "qualities": list(settings.QUALITIES)}

    @app.put("/api/settings")
    def put_settings(changes: dict):
        return {"preferences": settings.set_preferences(changes.get("preferences", changes)),
                "qualities": list(settings.QUALITIES)}

    return app
