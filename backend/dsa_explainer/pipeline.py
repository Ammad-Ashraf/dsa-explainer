"""The whole flow: plan -> verify -> quiz -> voice -> animation -> video,
and revisions of a finished lesson. Every lesson is verified again right
before rendering, so nothing unverified ever reaches the video."""

from __future__ import annotations

import re
import time
from datetime import datetime
from pathlib import Path

from . import config
from .authoring import planner, quiz, revise
from .core.lesson import Lesson
from .core.verifier import verify_lesson
from .media import video


def _quiet(msg: str, progress: float | None = None) -> None:
    print(msg)


def _new_dir(title: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40] or "lesson"
    path = config.OUTPUT_DIR / f"{datetime.now():%Y%m%d-%H%M%S}-{slug}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _finish(lesson: Lesson, folder: Path, version: int, quality: str, log, extra: dict) -> dict:
    report = verify_lesson(lesson)
    if not report.ok:
        raise planner.PlanError("The lesson failed verification: " + "; ".join(report.errors[:3]))
    (folder / "lesson.json").write_text(lesson.model_dump_json(indent=2), encoding="utf-8")
    result = video.build_video(lesson, report, folder / f"lesson_v{version}.mp4", quality, log)
    log("Done", 1.0)
    return {"lesson": lesson, "report": report, "folder": folder, "version": version, **extra, **result}


def make_lesson(topic: str, level: str = "beginner", quality: str = "draft", log=_quiet) -> dict:
    started = time.perf_counter()
    lesson, rejected = planner.plan_lesson(topic, level, log)
    plan_seconds = time.perf_counter() - started
    started = time.perf_counter()
    lesson.quiz = quiz.make_quiz(lesson, log=log)
    extra = {"rejected": rejected, "plan_seconds": plan_seconds, "quiz_seconds": time.perf_counter() - started}
    return _finish(lesson, _new_dir(lesson.title), 1, quality, log, extra)


def from_file(path: str | Path, quality: str = "draft", log=_quiet) -> dict:
    """Render a saved lesson plan (dsa_explainer/plans/*.json): no API needed."""
    lesson = Lesson.model_validate_json(Path(path).read_text(encoding="utf-8"))
    return _finish(lesson, _new_dir(lesson.title), 1, quality, log, {"rejected": []})


def revise_lesson(folder: str | Path, version: int, request: str, quality: str = "draft", log=_quiet) -> dict:
    folder = Path(folder)
    lesson = Lesson.model_validate_json((folder / "lesson.json").read_text(encoding="utf-8"))
    new, changed = revise.revise(lesson, request, log)
    return _finish(new, folder, version + 1, quality, log, {"changed": changed, "request": request})
