"""The whole flow: plan -> verify -> quiz -> voice -> animation -> video,
and revisions of a finished lesson. Every lesson is verified again right
before rendering, so nothing unverified ever reaches the video.

Progress goes to `log`: a plain function `log(message, fraction)` or an
events.Reporter, which also receives structured stage, scene and clip events.

A new lesson's quiz is written by the language model in a background thread
while the scenes are voiced and drawn; the quiz clips come last, so the quiz
call no longer adds its whole time to the wait. Every stage's time is saved
with the lesson (meta.json "timings").
"""

from __future__ import annotations

import contextvars
import shutil
import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

from . import config, events, store
from .authoring import planner, quiz, revise
from .core.lesson import Lesson
from .core.verifier import check_question, verify_lesson
from .media import video


def _finish(lesson: Lesson, folder: Path, version: int, quality: str, rep: events.Reporter, extra: dict,
            quiz_future: Future | None = None) -> dict:
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
        result = video.build_video(lesson, report, folder / f"lesson_v{version}.mp4", quality, rep, quiz=quiz_future)
    except BaseException:
        if new_folder:
            shutil.rmtree(folder, ignore_errors=True)  # no half-made lessons in the history
        else:
            (folder / f"lesson_v{version}.mp4").unlink(missing_ok=True)
        raise
    if quiz_future is not None:  # the quiz arrived during the build: verify the whole lesson once more
        report = verify_lesson(lesson)
        extra["quiz_seconds"] = rep.timings.get("quiz", 0.0)
    timings = {k: round(extra[k], 2) for k in ("plan_seconds", "quiz_seconds") if k in extra}
    timings.update(voice_seconds=round(result["voice_seconds"], 2), build_seconds=round(result["build_seconds"], 2))
    timings["stages"] = dict(rep.timings)  # wall-clock seconds of every stage, as the app showed them
    timings["spans"] = dict(rep.spans)  # when each stage ran: stages overlap (the quiz runs beside the drawing)
    timings["total"] = round(time.perf_counter() - extra.get("started", time.perf_counter()), 2)
    info = {
        "source": extra.get("source", "llm"), "quality": quality, "seconds": round(result["seconds"], 2),
        "clips": result["clips"], "rendered": result["rendered"], "reused": result["reused"],
        "chapters": result["chapters"], "checks": report.checks, "rejected": extra.get("rejected", []),
        "request": extra.get("request"), "changed": extra.get("changed", []), "timings": timings,
        "captions": bool(result.get("captions")) and Path(result["captions"]).is_file(),
    }
    store.save(folder, lesson, version, info)
    rep("Done", 1.0)
    return {"lesson": lesson, "report": report, "folder": folder, "lesson_id": folder.name, "version": version,
            **extra, **result}


def make_lesson(topic: str, level: str = "beginner", quality: str = "draft", log=None) -> dict:
    rep = events.reporter(log)
    rep.stage("plan", "running")
    started = job_started = time.perf_counter()
    try:
        lesson, rejected = planner.plan_lesson(topic, level, rep)
    except Exception as exc:
        rep.stage("plan", "failed", str(exc))
        raise
    plan_seconds = time.perf_counter() - started
    rep.stage("plan", "done", f"accepted after {len(rejected) + 1} attempt(s)")
    rep.check_cancelled()
    lesson.quiz = []
    extra = {"rejected": rejected, "plan_seconds": plan_seconds, "started": job_started}
    return _finish(lesson, config.OUTPUT_DIR / store.new_id(lesson.title), 1, quality, rep, extra,
                   quiz_future=start_quiz(lesson, rep))


def write_quiz(lesson: Lesson, rep: events.Reporter) -> list:
    """Verified questions for a lesson; questions built from the lesson if the language model fails."""
    rep.stage("quiz", "running")
    try:
        written = quiz.make_quiz(lesson.model_copy(deep=True), log=rep)
        questions = [q for q in written if check_question(lesson, q) is None]
        if not questions:
            raise ValueError("no question survived the verifier")
        rep.stage("quiz", "done", f"{len(questions)} verified question(s)")
        return questions
    except events.Cancelled:
        raise
    except Exception as exc:  # the lesson is verified and ready: a quiz problem must not throw it away
        questions = quiz.builtin_questions(lesson, 2)
        rep(f"The quiz writer failed ({str(exc)[:200]}); using questions built from the lesson.")
        rep.stage("quiz", "done", f"{len(questions)} built-in question(s) (the language model did not answer)")
        return questions


def start_quiz(lesson: Lesson, rep: events.Reporter) -> Future:
    """Write the quiz in a background thread (with this job's language-model settings) while the video is built."""
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="dsa-quiz")
    future = executor.submit(contextvars.copy_context().run, write_quiz, lesson, rep)
    executor.shutdown(wait=False)
    return future


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
