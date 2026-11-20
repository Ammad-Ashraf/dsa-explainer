"""How long a new lesson takes from "Make my lesson" to the finished video, stage by stage.

    python backend/scripts/latency_benchmark.py --plan stack --quiz-seconds 30
    python backend/scripts/latency_benchmark.py --plan bst --runs sequential,overlap --threads 0,2

The language model is replaced by a saved plan (planning takes no time here)
and by a quiz writer that waits --quiz-seconds before answering, like a real
provider (measure yours with scripts/eval_harness.py). Each run uses an empty
cache, so every scene is voiced and drawn. Runs:

  sequential  the order before Milestone 8: write the quiz, then voice and draw
  overlap     the quiz is written while the scenes are voiced and drawn

Prints a Markdown table: seconds to the first playable clip, to the finished
video, and per stage.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import time
from concurrent.futures import Future
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dsa_explainer import config, events, pipeline  # noqa: E402
from dsa_explainer.authoring import planner, quiz  # noqa: E402
from dsa_explainer.core.lesson import Lesson  # noqa: E402
from dsa_explainer.media.voices import ENGINES  # noqa: E402


class Clock(events.Reporter):
    def __init__(self) -> None:
        super().__init__(None)
        self.t0 = time.perf_counter()
        self.first_clip: float | None = None

    def emit(self, type: str, **data) -> None:
        if type == "clip" and self.first_clip is None:
            self.first_clip = time.perf_counter() - self.t0


def run(plan: str, mode: str, threads: int, quiz_seconds: float, quality: str) -> dict:
    lesson = Lesson.model_validate_json((config.PLANS_DIR / f"{plan}.json").read_text(encoding="utf-8"))
    questions = list(lesson.quiz)

    def slow_quiz(lesson, n=2, attempts=2, log=None):
        time.sleep(quiz_seconds)
        return questions

    def sequential(lesson, rep):  # the old order: the build starts only once the quiz exists
        future: Future = Future()
        future.set_result(pipeline.write_quiz(lesson, rep))
        return future

    config.VOICE_THREADS = threads
    for engine in ENGINES.values():  # reload the voice model with the new thread count
        if hasattr(engine, "_model"):
            engine._model = None
    original = (planner.plan_lesson, quiz.make_quiz, pipeline.start_quiz, config.CACHE_DIR, config.OUTPUT_DIR)
    with tempfile.TemporaryDirectory(dir=Path(config.CACHE_DIR).parent) as tmp:
        config.CACHE_DIR, config.OUTPUT_DIR = Path(tmp) / "cache", Path(tmp) / "outputs"
        planner.plan_lesson = lambda topic, level, log: (lesson.model_copy(deep=True), [])
        quiz.make_quiz = slow_quiz
        if mode == "sequential":
            pipeline.start_quiz = sequential
        clock = Clock()
        try:
            result = pipeline.make_lesson(lesson.topic, lesson.level, quality, clock)
        finally:
            planner.plan_lesson, quiz.make_quiz, pipeline.start_quiz, config.CACHE_DIR, config.OUTPUT_DIR = original
        total = time.perf_counter() - clock.t0
        shutil.rmtree(tmp, ignore_errors=True)
    return {"mode": mode, "threads": threads or "default", "first_clip": clock.first_clip, "total": total,
            "stages": clock.timings, "video": result["seconds"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plan", default="stack")
    parser.add_argument("--quiz-seconds", type=float, default=30.0)
    parser.add_argument("--runs", default="sequential,overlap")
    parser.add_argument("--threads", default="0", help="ONNX Runtime threads for the voice, comma-separated")
    parser.add_argument("--quality", default="draft")
    args = parser.parse_args()
    print(f"Plan {args.plan}, {args.quality} quality, {config.RENDER_WORKERS} drawing processes, quiz answers after "
          f"{args.quiz_seconds:.0f} s.\n")
    print("| Order | Voice threads | First clip playable | Finished video | Quiz | Voice | Draw | Join "
          "| Video length |")
    print("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for threads in [int(t) for t in args.threads.split(",")]:
        for mode in args.runs.split(","):
            r = run(args.plan, mode, threads, args.quiz_seconds, args.quality)
            s = r["stages"]
            print(f"| {mode} | {r['threads']} | {r['first_clip']:.0f} s | {r['total']:.0f} s | "
                  f"{s.get('quiz', 0):.0f} s | {s.get('voice', 0):.0f} s | {s.get('draw', 0):.0f} s | "
                  f"{s.get('join', 0):.0f} s | {r['video']:.0f} s |", flush=True)


if __name__ == "__main__":
    main()
