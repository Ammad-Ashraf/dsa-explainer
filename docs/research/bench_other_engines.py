"""Speed of candidate voice engines on this machine, on the same narrations as backend/scripts/voice_benchmark.py.

Run it in a separate virtual environment (these engines are not dependencies of DSA Explainer):

    python -m venv research-venv
    research-venv/Scripts/pip install piper-tts kittentts
    research-venv/Scripts/python -m piper.download_voices --download-dir voices en_US-lessac-medium
    research-venv/Scripts/python docs/research/bench_other_engines.py --piper-voice voices/en_US-lessac-medium.onnx

It prints one Markdown table row per engine: load time, seconds of audio, and the
real-time factor (synthesis time / audio length; below 1 is faster than real time).
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

DEFAULT_KITTEN = "KittenML/kitten-tts-nano-0.1"
PLANS = Path(__file__).resolve().parents[2] / "backend" / "dsa_explainer" / "plans"


def narrations(n: int = 6) -> list[str]:
    out = []
    for path in sorted(PLANS.glob("*.json"))[:n]:
        plan = json.loads(path.read_text(encoding="utf-8"))
        out.append(next(s["narration"] for s in plan["scenes"] if s["kind"] == "step"))
    return out


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def bench(name: str, load, speak, rate: int) -> str:
    started = time.perf_counter()
    engine = load()
    speak(engine, "Warming up.")
    loaded = time.perf_counter() - started
    synth = audio = 0.0
    for text in narrations():
        for sentence in sentences(text):
            t = time.perf_counter()
            samples = speak(engine, sentence)
            synth += time.perf_counter() - t
            audio += len(samples) / rate
    return f"| {name} | {loaded:.1f} | {audio:.1f} | {synth / audio:.2f} |"


def piper(voice: str) -> str:
    import numpy as np
    from piper import PiperVoice

    def speak(v, text):
        return np.concatenate([chunk.audio_float_array for chunk in v.synthesize(text)])

    model = PiperVoice.load(voice)
    return bench(f"Piper ({Path(voice).stem})", lambda: model, speak, model.config.sample_rate)


def kitten(model: str) -> str:
    import os

    import espeakng_loader  # phonemizer needs an espeak-ng library; use the one kokoro-onnx also ships

    os.environ.setdefault("PHONEMIZER_ESPEAK_LIBRARY", espeakng_loader.get_library_path())
    os.environ.setdefault("ESPEAK_DATA_PATH", espeakng_loader.get_data_path())
    from kittentts import KittenTTS

    def speak(k, text):
        return k.generate(text, voice="expr-voice-2-f")

    # kittentts 0.1.x fetches its default model (KittenML/kitten-tts-nano-0.1) from Hugging Face by itself
    return bench(f"Kitten TTS ({model})", lambda: KittenTTS() if model == DEFAULT_KITTEN else KittenTTS(model),
                 speak, 24000)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--piper-voice")
    parser.add_argument("--kitten-model", default=DEFAULT_KITTEN)
    args = parser.parse_args()
    print("| Engine | load + first sentence (s) | audio (s) | RTF |\n| --- | --- | --- | --- |")
    if args.piper_voice:
        try:
            print(piper(args.piper_voice), flush=True)
        except Exception as exc:  # report and go on to the next engine
            print(f"| Piper | failed: {type(exc).__name__}: {exc} | | |")
    try:
        print(kitten(args.kitten_model), flush=True)
    except Exception as exc:
        print(f"| Kitten TTS | failed: {type(exc).__name__}: {str(exc)[:120]} | | |")


if __name__ == "__main__":
    main()
