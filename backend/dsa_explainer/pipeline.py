"""The whole flow: plan -> verify -> quiz -> voice -> animation -> video,
and revisions of a finished lesson. Every lesson is verified again right
before rendering, so nothing unverified ever reaches the video.

Progress goes to `log`: a plain function `log(message, fraction)` or an
events.Reporter, which also receives structured stage, scene and clip events.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from . import config, events, store
from .authoring import planner, quiz, revise
from .core.lesson import Lesson
from .core.verifier import verify_lesson
from .media import video


def _finish(lesson: Lesson, folder: Path, version: int, quality: str, rep: events.Reporter, extra: dict) -> dict:
    rep.check_cancelled()
    rep.stage("verify", "running")
    report = verify_lesson(lesson)
    if not report.ok:
        rep.stage("verify", "failed", report.errors[0])
        raise planner.PlanError("The lesson failed verification: " + "; ".join(report.errors[:3]))
    rep.stage("verify", "done", f"{report.checks} checks passed")
    new_folder = not folder.exists()
    folder.mkdir(parents=True, exist_ok=True)
    try:
        result = video.build_video(lesson, report, folder / f"lesson_v{version}.mp4", quality, rep)
    except BaseException:
        if new_folder:
            shutil.rmtree(folder, ignore_errors=True)  # no half-made lessons in the history
        else:
            (folder / f"lesson_v{version}.mp4").unlink(missing_ok=True)
        raise
    timings = {k: round(extra[k], 2) for k in ("plan_seconds", "quiz_seconds") if k in extra}
    timings.update(voice_seconds=round(result["voice_seconds"], 2), build_seconds=round(result["build_seconds"], 2))
    info = {
        "source": extra.get("source", "llm"), "quality": quality, "seconds": round(result["seconds"], 2),
        "clips": result["clips"], "rendered": result["rendered"], "reused": result["reused"],
        "chapters": result["chapters"], "checks": report.checks, "rejected": extra.get("rejected", []),
        "request": extra.get("request"), "changed": extra.get("changed", []), "timings": timings,
    }
    store.save(folder, lesson, version, info)
    rep("Done", 1.0)
    return {"lesson": lesson, "report": report, "folder": folder, "lesson_id": folder.name, "version": version,
            **extra, **result}


def make_lesson(topic: str, level: str = "beginner", quality: str = "draft", log=None) -> dict:
    rep = events.reporter(log)
    rep.stage("plan", "running")
    started = time.perf_counter()
    try:
        lesson, rejected = planner.plan_lesson(topic, level, rep)
    except Exception as exc:
        rep.stage("plan", "failed", str(exc))
        raise
    plan_seconds = time.perf_counter() - started
    rep.stage("plan", "done", f"accepted after {len(rejected) + 1} attempt(s)")
    rep.check_cancelled()
    rep.stage("quiz", "running")
    started = time.perf_counter()
    lesson.quiz = quiz.make_quiz(lesson, log=rep)
    rep.stage("quiz", "done", f"{len(lesson.quiz)} verified question(s)")
    extra = {"rejected": rejected, "plan_seconds": plan_seconds, "quiz_seconds": time.perf_counter() - started}
    return _finish(lesson, config.OUTPUT_DIR / store.new_id(lesson.title), 1, quality, rep, extra)


def from_file(path: str | Path, quality: str = "draft", log=None) -> dict:
    """Render a saved lesson plan (dsa_explainer/plans/*.json): no API needed."""
    rep = events.reporter(log)
    path = Path(path)
    lesson = Lesson.model_validate_json(path.read_text(encoding="utf-8"))
    rep.stage("plan", "skipped", "saved lesson plan")
    rep.stage("quiz", "skipped", "saved with the plan")
    extra = {"rejected": [], "source": f"saved:{path.stem}"}
    return _finish(lesson, config.OUTPUT_DIR / store.new_id(lesson.title), 1, quality, rep, extra)


def revise_lesson(folder: str | Path, version: int, request: str, quality: str = "draft", log=None) -> dict:
    rep = events.reporter(log)
    folder = Path(folder)
    lesson = Lesson.model_validate_json((folder / "lesson.json").read_text(encoding="utf-8"))
    rep.stage("plan", "running", "revising")
    try:
        new, changed = revise.revise(lesson, request, rep)
    except Exception as exc:
        rep.stage("plan", "failed", str(exc))
        raise
    rep.stage("plan", "done", "changed " + ", ".join(changed))
    rep.stage("quiz", "skipped", "kept from the previous version")
    latest = max([v.get("version", 0) for v in store.read_meta(folder).get("versions", [])] + [version])
    return _finish(new, folder, latest + 1, quality, rep, {"changed": changed, "request": request})
