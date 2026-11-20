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
    GET  /api/lessons/{id}/captions/{version}  its captions (WebVTT)
    GET  /api/clips/{key}                    one finished clip, playable before the whole video is joined
    GET  /api/jobs, /api/jobs/{id}           job state
    GET  /api/jobs/{id}/events               Server-Sent Events: the job's progress, replayed then live
    POST /api/jobs/{id}/cancel
    GET/PUT /api/settings                    preferences
    GET  /api/voices                         the local voice engines and their voices
    POST /api/voices/preview                 a short sample of a voice (WAV)
    GET  /api/providers                      language-model presets and saved choices (never the keys)
    PUT  /api/providers/{id}                 save a key, model or address; optionally make it active
    POST /api/providers/active               choose the provider in use
    POST /api/providers/{id}/test            one tiny request with the saved or given settings
    GET  /api/providers/{id}/models          the models this key can use
"""

from __future__ import annotations

import asyncio
import json
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .. import config, pipeline, settings, store
from ..authoring import llm, providers
from ..core.lesson import Lesson, scene_labels
from .. import algorithms
from ..core.verifier import answer_index, verify_lesson
from ..media import voices
from .jobs import JobManager, JobReporter

Quality = Literal["draft", "standard", "high"]
LevelName = Literal["beginner", "intermediate", "advanced"]


class CreateLesson(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    level: LevelName = "beginner"
    quality: Quality | None = None


class RenderPlan(BaseModel):
    quality: Quality | None = None


class ProviderChoice(BaseModel):
    api_key: str | None = Field(default=None, max_length=500)
    model: str | None = Field(default=None, max_length=200)
    fallback_model: str | None = Field(default=None, max_length=200)
    base_url: str | None = Field(default=None, max_length=500)
    activate: bool = False


class ActiveProvider(BaseModel):
    provider: str | None


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
    return {"id": plan_id, "title": lesson.title, "topic": lesson.topic, "structure": algorithms.resolve(lesson.structure),
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
        why = {i: q.why_wrong[o] for i, o in enumerate(q.options) if o in q.why_wrong and i != right}
        quiz.append({"question": q.question, "options": q.options, "answer": right, "explanation": q.explanation,
                     "why_wrong": why})
    return {"scenes": scenes, "quiz": quiz,
            "verified": {"ok": report.ok, "checks": report.checks, "errors": report.errors[:5]},
            "plan": lesson.model_dump(mode="json")}


def _llm_public(s: llm.LLMSettings | None) -> dict:
    """What the page may know about the provider in use: never the key."""
    if s is None:
        return {"configured": False, "provider": None, "model": None, "base_url": None}
    preset = providers.PRESETS.get(s.provider)
    return {"configured": True, "provider": s.provider, "provider_name": preset.name if preset else "From .env",
            "model": s.model, "fallback_model": s.fallback_model, "base_url": s.base_url,
            "local": bool(preset and preset.local)}


# --- the app --------------------------------------------------------------------------


class VoicePreview(BaseModel):
    engine: str | None = None
    voice: str | None = Field(default=None, max_length=40)
    speed: float = Field(default=1.0, ge=0.7, le=1.3)


def _voice_ready() -> bool:
    try:
        return voices.engine().ready()
    except voices.VoiceError:
        return False


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

    @app.exception_handler(providers.ProviderError)
    async def bad_provider(_: Request, exc: providers.ProviderError):
        return JSONResponse({"detail": str(exc)}, status_code=400)

    @app.exception_handler(llm.LLMError)
    async def llm_problem(_: Request, exc: llm.LLMError):
        return JSONResponse({"detail": llm.redact(str(exc))}, status_code=502)

    # --- status and catalogue ---

    @app.get("/api/health")
    def health():
        return {
            "ok": True, "version": config.VERSION,
            "llm": _llm_public(llm.active_settings()),
            "voice": {"ready": _voice_ready(), "engine": config.VOICE_ENGINE, "voice": config.VOICE},
            "busy": any(j.status == "running" for j in jobs.list()),
        }

    @app.get("/api/catalog")
    def catalog():
        return {"categories": algorithms.CATEGORIES, "algorithms": algorithms.info()}

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
        chosen = llm.active_settings()  # fixed now: changing Settings later does not affect this job
        if chosen is None:
            raise HTTPException(400, "No language model is set up. Add an API key in Settings, or watch a saved lesson.")
        quality = _quality(body.quality)

        def run(rep: JobReporter) -> dict:
            with llm.use(chosen):
                result = pipeline.make_lesson(body.topic, body.level, quality, rep)
            return {"lesson_id": result["lesson_id"], "version": result["version"],
                    "model": llm.client_for(chosen).model_in_use()}

        params = {"topic": body.topic, "level": body.level, "quality": quality, "provider": chosen.provider,
                  "model": chosen.model}
        return jobs.submit("create", params, run).snapshot()

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
        chosen = llm.active_settings()
        if chosen is None and not pipeline.revise.is_rule_based(body.request):
            raise HTTPException(400, "Rewriting needs a language model. Speed changes ('slow down step 2') work "
                                     "without one.")
        latest = meta["versions"][-1]["version"] if meta.get("versions") else 1
        version = body.version or latest
        quality = _quality(body.quality)

        def run(rep: JobReporter) -> dict:
            with llm.use(chosen):
                result = pipeline.revise_lesson(path, version, body.request, quality, rep)
            return {"lesson_id": lesson_id, "version": result["version"], "changed": result.get("changed", [])}

        params = {"lesson_id": lesson_id, "request": body.request, "version": version, "quality": quality}
        return jobs.submit("revise", params, run).snapshot()

    @app.get("/api/lessons/{lesson_id}/videos/{version}")
    def video(lesson_id: str, version: int):
        return FileResponse(store.video(lesson_id, version), media_type="video/mp4")

    @app.get("/api/lessons/{lesson_id}/captions/{version}")
    def captions(lesson_id: str, version: int):
        return FileResponse(store.captions(lesson_id, version), media_type="text/vtt; charset=utf-8")

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

    # --- voices ---

    @app.get("/api/voices")
    def list_voices():
        engines = []
        for engine in voices.ENGINES.values():
            try:
                found = [v.to_dict() for v in engine.voices()]
            except voices.VoiceError:
                found = []
            engines.append({**engine.info(), "voices": found})
        return {"engines": engines, "current": {"engine": config.VOICE_ENGINE, "voice": config.VOICE,
                                                "speed": config.VOICE_SPEED}}

    @app.post("/api/voices/preview")
    def preview_voice(body: VoicePreview):
        try:
            path = voices.preview(body.engine, body.voice, body.speed)
        except voices.VoiceError as exc:
            raise HTTPException(400, str(exc)) from exc
        return FileResponse(path, media_type="audio/wav")

    # --- language-model providers ---

    @app.get("/api/providers")
    def list_providers():
        return {**providers.describe(), "in_use": _llm_public(llm.active_settings())}

    @app.put("/api/providers/{provider_id}")
    def save_provider(provider_id: str, body: ProviderChoice):
        providers.save(provider_id, body.model_dump(exclude={"activate"}, exclude_none=True), activate=body.activate)
        return list_providers()

    @app.post("/api/providers/active")
    def choose_provider(body: ActiveProvider):
        providers.activate(body.provider)
        return list_providers()

    def _client(provider_id: str, body: ProviderChoice | None) -> llm.Client:
        overrides = body.model_dump(exclude={"activate"}, exclude_none=True) if body else {}
        data = providers.resolve(provider_id, overrides)
        if data is None:
            preset = providers.PRESETS.get(provider_id)
            need = "an API key and a model" if preset is None or preset.needs_key else "a model"
            raise HTTPException(400, f"Give {need} first.")
        # a fresh client, so a test never inherits another configuration's fallback state
        return llm.Client(llm.LLMSettings.from_dict(data))

    @app.post("/api/providers/{provider_id}/test")
    def test_provider(provider_id: str, body: ProviderChoice | None = None):
        client = _client(provider_id, body)
        try:
            return client.check()
        except llm.LLMError as exc:
            return {"ok": False, "error": llm.redact(str(exc), providers.secrets() + [client.settings.api_key])}
        except Exception as exc:  # report it, never leak a key
            text = f"{exc.__class__.__name__}: {exc}"
            return {"ok": False, "error": llm.redact(text, providers.secrets() + [client.settings.api_key])[:500]}

    @app.get("/api/providers/{provider_id}/models")
    def provider_models(provider_id: str):
        return {"models": _client(provider_id, None).list_models()}

    _serve_web_app(app)
    return app


NO_WEB_APP = """<!doctype html><meta charset="utf-8"><title>DSA Explainer</title>
<body style="font-family:system-ui;max-width:640px;margin:80px auto;line-height:1.5;color:#4b4b4b">
<h1 style="color:#58cc02">DSA Explainer is running</h1>
<p>The API is up, but the web app has not been built yet. Build it once with:</p>
<pre style="background:#f7f7f7;padding:12px;border-radius:12px">cd frontend
npm install
npm run build</pre>
<p>Then reload this page. The API reference is at <a href="/api/docs">/api/docs</a>.</p></body>"""


def _serve_web_app(app: FastAPI) -> None:
    """Serve the built React app; every non-API path falls back to index.html (client-side routes)."""
    web = config.FRONTEND_DIR.resolve()
    if (web / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=web / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def web_app(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, f"no API route /{path}")
        if not (web / "index.html").is_file():
            return HTMLResponse(NO_WEB_APP)
        file = (web / path).resolve()
        if path and file.is_file() and web in file.parents:
            return FileResponse(file)
        return FileResponse(web / "index.html", headers={"Cache-Control": "no-cache"})
