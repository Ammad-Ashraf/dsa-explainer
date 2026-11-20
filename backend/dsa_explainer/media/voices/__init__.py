"""Narration voices: pluggable local engines, a pronunciation lexicon, timings and captions.

`speak(text)` turns one scene's narration into a WAV file. The narration is
split into sentences; each sentence is read through the lexicon and spoken by
the chosen engine, and the sentences are joined with a short pause. Because
every sentence is synthesised on its own, its start and end in the audio are
known exactly; captions are cut from them (long sentences are split at commas,
timed by their share of the letters). The WAV and its caption cues are cached
by a hash of everything that changes the sound, so unchanged narration is never
spoken twice.

Engines live in ENGINES; Kokoro is the first. See docs/research/voice-models.md.
"""

from __future__ import annotations

import hashlib
import json
import re
import wave
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ... import config
from . import lexicon
from .base import Engine, Voice, VoiceError
from .kokoro import KokoroEngine

ENGINES: dict[str, Engine] = {e.name: e for e in (KokoroEngine(),)}
SENTENCE_PAUSE = 0.25  # seconds of silence between sentences (what Kokoro itself puts between them)
CAPTION_WORDS = 12  # a caption longer than this is split at a comma, or between words
PREVIEW_TEXT = ("Push seven onto the stack. The top is now seven, and the stack holds three values. "
                "Breadth-first search visits nodes in O(V + E) time.")

__all__ = ["ENGINES", "PREVIEW_TEXT", "Engine", "Speech", "Voice", "VoiceError", "captions_vtt", "engine", "preview",
           "sentences", "silence", "speak"]


@dataclass
class Speech:
    path: str
    seconds: float
    cues: list = field(default_factory=list)  # [start, end, text] in seconds from the start of the audio


def engine(name: str | None = None) -> Engine:
    name = name or config.VOICE_ENGINE
    if name not in ENGINES:
        raise VoiceError(f"unknown voice engine '{name}'; use one of: {', '.join(ENGINES)}")
    return ENGINES[name]


def sentences(text: str) -> list[str]:
    """Narration split after . ! or ? (not inside numbers like 2.5)."""
    parts = re.split(r"(?<=[.!?])\s+(?=\S)", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _chunks(sentence: str) -> list[str]:
    """A sentence cut into caption-sized pieces, preferring commas."""
    words = sentence.split()
    if len(words) <= CAPTION_WORDS:
        return [sentence]
    pieces, current = [], []
    for word in words:
        current.append(word)
        if (word.endswith((",", ";", ":")) and len(current) >= 4) or len(current) >= CAPTION_WORDS:
            pieces.append(" ".join(current))
            current = []
    if current:
        if len(current) < 3 and pieces and len(pieces[-1].split()) + len(current) <= CAPTION_WORDS:
            pieces[-1] += " " + " ".join(current)
        else:
            pieces.append(" ".join(current))
    return pieces


def _cues(spans: list[tuple[float, float, str]]) -> list[list]:
    cues = []
    for start, end, sentence in spans:
        pieces = _chunks(sentence)
        letters = sum(len(p) for p in pieces) or 1
        at = start
        for piece in pieces:
            length = (end - start) * len(piece) / letters
            cues.append([round(at, 3), round(at + length, 3), piece])
            at += length
    return cues


def _key(text: str, speed: float, voice: str, eng: Engine) -> str:
    parts = f"{eng.name}|{eng.version}|{lexicon.VERSION}|{voice}|{speed}|{text}"
    return hashlib.sha1(parts.encode()).hexdigest()[:20]


def _write_wav(path: Path, samples: np.ndarray, rate: int) -> None:
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    with wave.open(str(tmp), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    tmp.replace(path)


def duration(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def speak(text: str, speed: float = 1.0, voice: str | None = None, engine_name: str | None = None) -> Speech:
    """Narration -> a cached WAV file, its length and its caption cues."""
    eng = engine(engine_name)
    voice = voice or config.VOICE
    speed = round(speed * config.VOICE_SPEED, 3)
    key = _key(text, speed, voice, eng)
    path = config.CACHE_DIR / "audio" / f"{key}.wav"
    cues_file = path.with_suffix(".json")
    if not (path.exists() and cues_file.exists()):
        parts, spans, at = [], [], 0.0
        gap = np.zeros(int(eng.sample_rate * SENTENCE_PAUSE), dtype=np.float32)
        for sentence in sentences(text) or [text]:
            spoken = lexicon.speakable(sentence)
            if not spoken:
                continue
            if parts:
                parts.append(gap)
                at += SENTENCE_PAUSE
            samples = eng.synthesize(spoken, voice, speed)
            seconds = len(samples) / eng.sample_rate
            parts.append(samples)
            spans.append((at, at + seconds, sentence))
            at += seconds
        if not parts:
            raise VoiceError("there is nothing to say")
        _write_wav(path, np.concatenate(parts), eng.sample_rate)
        cues_file.write_text(json.dumps(_cues(spans)), encoding="utf-8")
    return Speech(str(path), duration(path), json.loads(cues_file.read_text(encoding="utf-8")))


def preview(engine_name: str | None = None, voice: str | None = None, speed: float = 1.0,
            text: str = PREVIEW_TEXT) -> Path:
    """A short sample of a voice, for the settings page."""
    eng = engine(engine_name)
    voice = voice or config.VOICE
    if voice not in {v.id for v in eng.voices()}:
        raise VoiceError(f"{eng.title} has no voice '{voice}'")
    return Path(speak(text, speed / config.VOICE_SPEED, voice, eng.name).path)


def silence(seconds: float = 0.02) -> str:
    """A short silent WAV, used to pad a clip's audio to its full length."""
    path = config.CACHE_DIR / "audio" / f"silence_{int(seconds * 1000)}ms.wav"
    if not path.exists():
        _write_wav(path, np.zeros(int(24000 * seconds), dtype=np.float32), 24000)
    return str(path)


def _stamp(t: float) -> str:
    ms = int(round(max(0.0, t) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def captions_vtt(cues: list) -> str:
    """WebVTT for [start, end, text] cues."""
    lines = ["WEBVTT", ""]
    for i, (start, end, text) in enumerate(cues, 1):
        lines += [str(i), f"{_stamp(start)} --> {_stamp(end)}", text.replace("-->", "->"), ""]
    return "\n".join(lines)
