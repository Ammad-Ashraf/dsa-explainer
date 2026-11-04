"""From a verified lesson to one mp4.

1. Narration audio for every scene (Kokoro, local, cached by text).
2. One Manim clip per scene, cached by a hash of everything that clip shows,
   so after a revision only the scenes that changed are rendered again.
3. ffmpeg joins the clips without re-encoding.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import av
import imageio_ffmpeg

from . import config, voice
from .lesson import Lesson, scene_labels
from .render import RENDER_VERSION, render_clip
from .verifier import Report, answer_index


def jobs_for(lesson: Lesson, report: Report) -> list[dict]:
    """Everything the renderer needs for each clip, as plain data."""
    labels = scene_labels(lesson)
    steps = sum(s.kind == "step" for s in lesson.scenes)
    jobs = []
    for name, scene, frame in zip(labels, lesson.scenes, report.frames):
        header = f"Step {name.split()[1]} of {steps}" if scene.kind == "step" else name.title()
        jobs.append({
            "name": name, "kind": scene.kind, "structure": lesson.structure, "title": lesson.title,
            "level": lesson.level, "label": header if scene.kind != "intro" else "", "caption": scene.caption,
            "points": scene.points, "narration": scene.narration, "speed": scene.speed,
            "before": frame.before, "after": frame.after, "focus": frame.focus,
        })
    for i, q in enumerate(lesson.quiz, 1):
        right = answer_index(lesson, q)
        spoken = [f"{letter}: {text}" for letter, text in zip("ABCD", q.options)]
        choices = ", ".join(spoken[:-1]) + ", or " + spoken[-1]
        jobs.append({
            "name": f"quiz {i}", "kind": "quiz", "structure": lesson.structure, "title": lesson.title,
            "label": f"Quiz {i} of {len(lesson.quiz)}", "question": q.question, "options": q.options,
            "answer": right, "speed": 1.0,
            "narration": f"Quiz time. {q.question} Is it {choices}?",
            "answer_narration": f"The answer is {'ABCD'[right]}, {q.options[right]}. {q.explanation}",
        })
    return jobs


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


def build_video(lesson: Lesson, report: Report, out: Path, quality: str = "draft", log=print) -> dict:
    jobs = jobs_for(lesson, report)
    clips, futures, voice_seconds = [], {}, 0.0
    started = time.perf_counter()
    # The voice runs here; each clip goes to a drawing process as soon as its audio
    # exists, so speaking and drawing overlap, and several clips are drawn at once.
    with ProcessPoolExecutor(max_workers=config.RENDER_WORKERS) as pool:
        for i, job in enumerate(jobs):
            log(f"Speaking {job['name']} ({i + 1}/{len(jobs)})", 0.35 + 0.3 * i / len(jobs))
            spoken = time.perf_counter()
            job["audio"], job["duration"] = voice.speak(job["narration"], job["speed"])
            if job["kind"] == "quiz":
                job["answer_audio"], job["answer_duration"] = voice.speak(job["answer_narration"])
            voice_seconds += time.perf_counter() - spoken
            clips.append(clip_path(job, quality))
            if not clips[-1].exists():
                futures[pool.submit(render_clip, job, clips[-1], quality)] = job["name"]
        for done, future in enumerate(as_completed(futures), 1):
            future.result()  # re-raises a drawing error
            log(f"Drew {futures[future]} ({done}/{len(futures)} clips)", 0.65 + 0.3 * done / len(futures))
    build_seconds = time.perf_counter() - started

    log("Joining the clips", 0.97)
    out.parent.mkdir(parents=True, exist_ok=True)
    concat(clips, out)
    rendered = list(futures.values())
    return {
        "video": out, "seconds": clip_seconds(out), "clips": len(clips), "rendered": rendered,
        "reused": len(clips) - len(rendered), "voice_seconds": voice_seconds, "build_seconds": build_seconds,
    }
