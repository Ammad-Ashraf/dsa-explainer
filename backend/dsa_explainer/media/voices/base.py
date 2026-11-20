"""What every voice engine provides.

An engine turns one sentence into audio on this machine. Everything else (the
pronunciation lexicon, splitting narration into sentences, caching, timings and
captions) is shared and lives in voices/__init__.py, so a new engine only has to
implement `voices()` and `synthesize()`. See docs/research/voice-models.md for
the engines considered and how they were measured.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


class VoiceError(RuntimeError):
    """The engine cannot speak: its model is missing, or the voice is unknown."""


@dataclass(frozen=True)
class Voice:
    id: str
    name: str
    language: str  # BCP 47, e.g. "en-US"
    gender: str = ""  # "female", "male" or ""

    def to_dict(self) -> dict:
        return asdict(self)


class Engine:
    name = ""  # registry key, stored in settings
    title = ""  # shown in the app
    licence = ""  # of the code and of the weights, in one line
    version = "1"  # part of the audio cache key: change it when the same text would sound different
    sample_rate = 24000

    def ready(self) -> bool:
        """True when the model files are on disk (nothing is downloaded on demand)."""
        raise NotImplementedError

    def setup_hint(self) -> str:
        """What to do when the engine is not ready."""
        return ""

    def voices(self) -> list[Voice]:
        raise NotImplementedError

    def synthesize(self, text: str, voice: str, speed: float = 1.0) -> np.ndarray:
        """One sentence of plain text -> mono float32 samples at `sample_rate`."""
        raise NotImplementedError

    def info(self) -> dict:
        return {"id": self.name, "title": self.title, "licence": self.licence, "ready": self.ready(),
                "setup": "" if self.ready() else self.setup_hint()}
