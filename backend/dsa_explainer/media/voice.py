"""Narration voice: Kokoro-82M through ONNX, on the local CPU (no API).

Each narration becomes a WAV file named by a hash of its text, voice and
speed, so a scene whose narration did not change is never synthesised again.
"""

from __future__ import annotations

import hashlib
import logging
import re
import threading
import wave
from pathlib import Path

import numpy as np

from .. import config

_engine = None
_lock = threading.Lock()  # Kokoro's phonemizer is not thread-safe
logging.getLogger("phonemizer").setLevel(logging.ERROR)  # harmless "words count mismatch" notes


def _kokoro():
    global _engine
    if _engine is None:
        if not config.KOKORO_MODEL.exists() or not config.KOKORO_VOICES.exists():
            raise FileNotFoundError("Kokoro voice files are missing: run  python backend/scripts/download_models.py")
        from kokoro_onnx import Kokoro

        _engine = Kokoro(str(config.KOKORO_MODEL), str(config.KOKORO_VOICES))
    return _engine


def speakable(text: str) -> str:
    """Text as it should be read: O(n) -> 'O of n', no symbols."""
    text = re.sub(r"\bO\s*\(\s*([^)]*)\)", lambda m: "O of " + m.group(1).replace("^", " to the "), text)
    return re.sub(r"[*_#`\[\]{}]", "", text).replace("->", " to ").strip()


def duration(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def speak(text: str, speed: float = 1.0) -> tuple[str, float]:
    """Narration -> (path of a WAV file, seconds of audio)."""
    key = hashlib.sha1(f"{config.KOKORO_VOICE}|{speed}|{text}".encode()).hexdigest()[:20]
    path = config.CACHE_DIR / "audio" / f"{key}.wav"
    if not path.exists():
        with _lock:
            samples, rate = _kokoro().create(speakable(text), voice=config.KOKORO_VOICE, speed=speed, lang="en-us")
        pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".part")
        with wave.open(str(tmp), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(pcm.tobytes())
        tmp.replace(path)
    return str(path), duration(path)


def silence(seconds: float = 0.02) -> str:
    """A short silent WAV, used to pad a clip's audio to its full length."""
    path = config.CACHE_DIR / "audio" / f"silence_{int(seconds * 1000)}ms.wav"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(np.zeros(int(24000 * seconds), dtype=np.int16).tobytes())
    return str(path)
