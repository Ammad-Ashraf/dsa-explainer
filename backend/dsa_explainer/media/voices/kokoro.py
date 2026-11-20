"""Kokoro-82M through ONNX Runtime, on the local CPU (or a GPU provider when one is installed).

Weights: Apache-2.0 (hexgrad/Kokoro-82M). Runtime: kokoro-onnx (MIT), which
phonemises with espeak-ng (GPL-3.0) through phonemizer and espeakng-loader;
docs/research/voice-models.md records what that means for this MIT project.
"""

from __future__ import annotations

import logging
import threading

import numpy as np

from ... import config
from .base import Engine, Voice, VoiceError

logging.getLogger("phonemizer").setLevel(logging.ERROR)  # harmless "words count mismatch" notes

ACCENTS = {"a": ("en-US", "American English"), "b": ("en-GB", "British English")}
GENDERS = {"f": "female", "m": "male"}


class KokoroEngine(Engine):
    name, title = "kokoro", "Kokoro-82M"
    licence = "weights Apache-2.0; kokoro-onnx MIT; espeak-ng phonemiser GPL-3.0 (installed separately)"
    version = "1"
    sample_rate = 24000

    def __init__(self) -> None:
        self._model = None
        self._lock = threading.Lock()  # the phonemiser is not thread-safe

    def ready(self) -> bool:
        return config.KOKORO_MODEL.exists() and config.KOKORO_VOICES.exists()

    def setup_hint(self) -> str:
        return "Download the voice model: python backend/scripts/download_models.py"

    def _load(self):
        if self._model is None:
            if not self.ready():
                raise VoiceError("Kokoro voice files are missing. " + self.setup_hint())
            import onnxruntime as ort
            from kokoro_onnx import Kokoro

            options = ort.SessionOptions()
            if config.VOICE_THREADS:  # 0 lets ONNX Runtime choose (one thread per physical core)
                options.intra_op_num_threads = config.VOICE_THREADS
            available = ort.get_available_providers()
            providers = [p for p in config.VOICE_PROVIDERS if p in available] or ["CPUExecutionProvider"]
            session = ort.InferenceSession(str(config.KOKORO_MODEL), sess_options=options, providers=providers)
            self._model = Kokoro.from_session(session, str(config.KOKORO_VOICES))
        return self._model

    def voices(self) -> list[Voice]:
        if not self.ready():
            return []
        ids = sorted(self._load().get_voices())
        out = []
        for vid in ids:
            accent, gender = (vid[:1], vid[1:2]) if len(vid) > 3 and vid[2] == "_" else ("", "")
            if accent not in ACCENTS:
                continue  # Kokoro also has voices for other languages; the lessons are in English
            name = vid[3:].replace("_", " ").title()
            out.append(Voice(vid, f"{name} ({ACCENTS[accent][1]})", ACCENTS[accent][0], GENDERS.get(gender, "")))
        return out

    def synthesize(self, text: str, voice: str, speed: float = 1.0) -> np.ndarray:
        model = self._load()
        if voice not in model.get_voices():
            raise VoiceError(f"Kokoro has no voice '{voice}'")
        lang = "en-gb" if voice.startswith("b") else "en-us"
        with self._lock:
            samples, rate = model.create(text, voice=voice, speed=speed, lang=lang)
        if rate != self.sample_rate:
            raise VoiceError(f"Kokoro returned {rate} Hz audio, expected {self.sample_rate}")
        return np.asarray(samples, dtype=np.float32)
