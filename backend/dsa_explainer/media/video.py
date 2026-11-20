"""From a verified lesson to one mp4.

1. Narration audio for every scene (a local voice engine, cached by text),
   with caption cues timed from the sentences it spoke.
2. One Manim clip per scene, cached by a hash of everything that clip shows,
   so after a revision only the scenes that changed are rendered again.
3. ffmpeg joins the clips without re-encoding; the captions are joined into
   one WebVTT file with the same offsets.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from pathlib import Path

import av
import imageio_ffmpeg

from .. import algorithms, config, events
from ..core.lesson import Lesson, scene_labels
from ..core.verifier import Report, answer_index
from . import voices
from .render import QUIZ_INTRO_SECONDS, RENDER_VERSION, THINK_SECONDS, render_clip


QUIZ_SIZE = 2  # questions a new lesson usually gets (only for progress, until the quiz is written)


def _common(lesson: Lesson) -> dict:
    cls = algorithms.get(lesson.structure)
    return {"structure": cls.NAME, "view": cls.VIEW, "structure_title": cls.TITLE, "title": lesson.title}


def jobs_for(lesson: Lesson, report: Report) -> list[dict]:
    """Everything the renderer needs for each clip (scenes, then quiz questions), as plain data."""
    return scene_jobs(lesson, report) + quiz_jobs(lesson)


def scene_jobs(lesson: Lesson, report: Report) -> list[dict]:
    labels = scene_labels(lesson)
    steps = sum(s.kind == "step" for s in lesson.scenes)
    common = _common(lesson)
    code = list(algorithms.get(lesson.structure).PSEUDOCODE)
    jobs = []
    for name, scene, frame in zip(labels, lesson.scenes, report.frames):
        header = f"Step {name.split()[1]} of {steps}" if scene.kind == "step" else name.title()
        jobs.append({
            "name": name, "kind": scene.kind, **common, "level": lesson.level, "label": header if scene.kind != "intro" else "", "caption": scene.caption,
            "points": scene.points, "narration": scene.narration, "speed": scene.speed,
            "before": frame.before, "after": frame.after, "focus": frame.focus,
            # beside the picture: the pseudocode with the lines this step ran, and the facts strip
            "code": code, "lines": frame.lines, "strip_before": frame.strip_before, "strip_after": frame.strip_after,
        })
    return jobs


def quiz_jobs(lesson: Lesson) -> list[dict]:
    common, jobs = _common(lesson), []
    for i, q in enumerate(lesson.quiz, 1):
        right = answer_index(lesson, q)
        spoken = [f"{letter}: {text}" for letter, text in zip("ABCD", q.options)]
        choices = ", ".join(spoken[:-1]) + ", or " + spoken[-1]
        jobs.append({
            "name": f"quiz {i}", "kind": "quiz", **common,
            "label": f"Quiz {i} of {len(lesson.quiz)}", "question": q.question, "options": q.options,
            "answer": right, "speed": 1.0,
            "narration": f"Quiz time. {q.question} Is it {choices}?",
            "answer_narration": f"The answer is {'ABCD'[right]}, {q.options[right]}. {q.explanation}",
        })
    return jobs


def quiz_reveal(question_seconds: float) -> float:
    """When a quiz clip starts speaking the answer (render.LessonScene.play_quiz): after the question is read,
    the options have appeared, and the thinking time has run out."""
    return max(QUIZ_INTRO_SECONDS, question_seconds + 0.3) + THINK_SECONDS


def clip_seconds(path: Path) -> float:
    with av.open(str(path)) as container:
        return container.duration / 1_000_000


def concat(clips: list[Path], out: Path) -> None:
    listing = out.with_suffix(".txt")
    listing.write_text("".join(f"file '{c.resolve().as_posix()}'\n" for c in clips), encoding="utf-8")
    subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(listing), "-c", "copy", "-movflags", "+faststart", str(out)],
        check=True,
    )
    listing.unlink()


def clip_path(job: dict, quality: str) -> Path:
    """Cache file for a clip, named by everything the clip shows and says."""
    fingerprint = json.dumps({k: v for k, v in job.items() if k != "name"}, sort_keys=True, default=str)
    key = hashlib.sha1(f"{RENDER_VERSION}|{quality}|{fingerprint}".encode()).hexdigest()[:20]
    return config.CACHE_DIR / "clips" / f"{key}.mp4"


def build_video(lesson: Lesson, report: Report, out: Path, quality: str = "draft", log=None,
                quiz: Future | None = None) -> dict:
    """Voice, draw and join every clip. With `quiz` (a Future of verified questions, written while this runs),
    the lesson's scenes are voiced and drawn first and the quiz clips are added once the questions are ready."""
    rep = events.reporter(log)
    jobs = scene_jobs(lesson, report) if quiz is not None else jobs_for(lesson, report)
    total = len(jobs) + (QUIZ_SIZE if quiz is not None else 0)
    clips, futures, voice_seconds, cues = [], {}, 0.0, []
    started = time.perf_counter()

    def clip_ready(index: int, cached: bool) -> None:
        rep.emit("clip", index=index, total=total, name=jobs[index]["name"], key=clips[index].stem,
                 seconds=round(clip_seconds(clips[index]), 2), cached=cached, cues=cues[index])

    reported: set = set()

    def report_finished() -> None:
        """Announce clips that finished drawing, so playback can start while later scenes are still voiced."""
        for future in [f for f in futures if f.done() and f not in reported]:
            future.result()  # re-raises a drawing error
            reported.add(future)
            i = futures[future]
            rep.emit("scene", stage="draw", index=i, total=total, name=jobs[i]["name"])
            clip_ready(i, cached=False)

    # The voice runs here; each clip goes to a drawing process as soon as its audio
    # exists, so speaking and drawing overlap, and several clips are drawn at once.
    pool = ProcessPoolExecutor(max_workers=config.RENDER_WORKERS)
    try:
        rep.stage("voice", "running")
        rep.stage("draw", "running")
        i = 0
        while i < len(jobs) or quiz is not None:
            if i == len(jobs):  # every scene is voiced: now the quiz clips, as soon as the questions exist
                while not quiz.done():
                    rep.check_cancelled()
                    report_finished()
                    time.sleep(0.2)
                lesson.quiz = quiz.result()
                quiz = None
                jobs += quiz_jobs(lesson)
                total = len(jobs)
                continue
            job = jobs[i]
            rep.check_cancelled()
            report_finished()
            rep.emit("scene", stage="voice", index=i, total=total, name=job["name"])
            rep(f"Speaking {job['name']} ({i + 1}/{total})", 0.35 + 0.3 * i / total)
            spoken = time.perf_counter()
            speech = voices.speak(job["narration"], job["speed"])
            job["audio"], job["duration"] = speech.path, speech.seconds
            job_cues = list(speech.cues)
            if job["kind"] == "quiz":
                answer = voices.speak(job["answer_narration"])
                job["answer_audio"], job["answer_duration"] = answer.path, answer.seconds
                at = quiz_reveal(job["duration"])
                job_cues += [[s + at, e + at, text] for s, e, text in answer.cues]
            cues.append(job_cues)
            voice_seconds += time.perf_counter() - spoken
            clips.append(clip_path(job, quality))
            if clips[-1].exists():
                clip_ready(i, cached=True)
            else:
                futures[pool.submit(render_clip, job, clips[-1], quality)] = i
            i += 1
        rep.stage("voice", "done", f"{total} scenes")
        for future in as_completed(futures):
            rep.check_cancelled()
            if future in reported:
                continue
            future.result()  # re-raises a drawing error
            reported.add(future)
            i = futures[future]
            rep.emit("scene", stage="draw", index=i, total=total, name=jobs[i]["name"])
            rep(f"Drew {jobs[i]['name']} ({len(reported)}/{len(futures)} clips)", 0.65 + 0.3 * len(reported) / len(futures))
            clip_ready(i, cached=False)
        rep.stage("draw", "done", f"{len(futures)} drawn, {total - len(futures)} reused")
    except BaseException:
        pool.shutdown(wait=False, cancel_futures=True)
        raise
    pool.shutdown()
    build_seconds = time.perf_counter() - started

    rep.check_cancelled()
    rep.stage("join", "running")
    rep("Joining the clips", 0.97)
    out.parent.mkdir(parents=True, exist_ok=True)
    concat(clips, out)
    marks = chapters(jobs, clips)
    lesson_cues = [[round(s + mark["start"], 3), round(e + mark["start"], 3), text]
                   for mark, clip_cues in zip(marks, cues) for s, e, text in clip_cues]
    out.with_suffix(".vtt").write_text(voices.captions_vtt(lesson_cues), encoding="utf-8")
    rendered = [jobs[i]["name"] for i in futures.values()]
    seconds = clip_seconds(out)
    rep.stage("join", "done", f"{seconds:.0f} s video")
    return {
        "video": out, "seconds": seconds, "clips": len(clips), "rendered": rendered,
        "reused": len(clips) - len(rendered), "voice_seconds": voice_seconds, "build_seconds": build_seconds,
        "clip_keys": [c.stem for c in clips], "chapters": marks, "captions": out.with_suffix(".vtt"),
    }


def chapters(jobs: list[dict], clips: list[Path]) -> list[dict]:
    """Where each scene starts in the joined video, for the player's chapter strip."""
    out, at = [], 0.0
    for job, clip in zip(jobs, clips):
        length = clip_seconds(clip)
        out.append({"name": job["name"], "kind": job["kind"], "start": round(at, 2), "seconds": round(length, 2)})
        at += length
    return out
