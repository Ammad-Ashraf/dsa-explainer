"""Measure the voice engine on this machine: real-time factor by ONNX Runtime thread count.

    python backend/scripts/voice_benchmark.py                # Kokoro, default threads and 1, 2, 4, all
    python backend/scripts/voice_benchmark.py --threads 0 2  # only these (0 = ONNX Runtime's default)

The real-time factor (RTF) is synthesis time divided by audio length: below 1 is
faster than real time. Each setting speaks the same narrations (taken from the
saved plans) after one warm-up sentence; results go to stdout as a Markdown table.
"""

from __future__ import annotations

import argparse
import os
import platform
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dsa_explainer import config  # noqa: E402
from dsa_explainer.core.lesson import Lesson  # noqa: E402
from dsa_explainer.media.voices import lexicon, sentences  # noqa: E402
from dsa_explainer.media.voices.kokoro import KokoroEngine  # noqa: E402


def narrations(n: int) -> list[str]:
    out = []
    for path in sorted(config.PLANS_DIR.glob("*.json"))[:n]:
        lesson = Lesson.model_validate_json(path.read_text(encoding="utf-8"))
        out.append(next(s.narration for s in lesson.scenes if s.kind == "step"))
    return out


def measure(threads: int, texts: list[str], voice: str) -> dict:
    config.VOICE_THREADS = threads
    engine = KokoroEngine()
    started = time.perf_counter()
    engine.synthesize("Warming up.", voice)
    load = time.perf_counter() - started
    synth, audio, per_sentence = 0.0, 0.0, []
    for text in texts:
        for sentence in sentences(text):
            t = time.perf_counter()
            samples = engine.synthesize(lexicon.speakable(sentence), voice)
            spent = time.perf_counter() - t
            seconds = len(samples) / engine.sample_rate
            synth, audio = synth + spent, audio + seconds
            per_sentence.append(spent / seconds)
    return {"threads": threads or "default", "load": load, "rtf": synth / audio, "audio": audio,
            "median": statistics.median(per_sentence)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--threads", type=int, nargs="*", default=[0, 1, 2, 4, os.cpu_count() or 4])
    parser.add_argument("--plans", type=int, default=6, help="how many saved plans to take a narration from")
    parser.add_argument("--voice", default="af_heart")
    args = parser.parse_args()
    texts = narrations(args.plans)
    print(f"CPU: {platform.processor() or platform.machine()} ({os.cpu_count()} logical cores), "
          f"{platform.system()} {platform.release()}, Python {platform.python_version()}")
    import onnxruntime

    print(f"ONNX Runtime {onnxruntime.__version__}; {sum(len(t.split()) for t in texts)} words of narration\n")
    print("| threads | load + first sentence (s) | audio (s) | RTF overall | RTF median per sentence |")
    print("| --- | --- | --- | --- | --- |")
    for threads in dict.fromkeys(args.threads):
        r = measure(threads, texts, args.voice)
        print(f"| {r['threads']} | {r['load']:.1f} | {r['audio']:.1f} | {r['rtf']:.2f} | {r['median']:.2f} |",
              flush=True)


if __name__ == "__main__":
    main()
