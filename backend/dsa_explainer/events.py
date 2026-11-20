"""Progress events from the pipeline.

Every stage reports through one object, the reporter. The pipeline's stages are
STAGES, in order. Event types:

  stage     {"stage", "status": running | done | failed | skipped, "detail"?, "seconds"?}
  message   {"text", "fraction"?}            free text, with overall progress 0..1
  rejected  {"stage", "attempt", "reason"}   the verifier sent a plan, quiz or revision back
  scene     {"stage", "index", "total", "name"}  per-scene progress of voice and drawing
  clip      {"index", "total", "name", "key", "seconds", "cached"}  a finished clip, playable now

Old callers pass a plain function `log(message, fraction=None)`; `reporter()`
wraps it so they keep working and simply see the text of every event.
"""

from __future__ import annotations

import time
from collections.abc import Callable

STAGES = ("plan", "verify", "quiz", "voice", "draw", "join")
STAGE_NAMES = {"plan": "Plan", "verify": "Verify", "quiz": "Quiz", "voice": "Voice", "draw": "Draw", "join": "Join"}


class Cancelled(RuntimeError):
    """The learner cancelled the job."""


class Reporter:
    """Base reporter: turns every event into one line of text for `on_text`."""

    def __init__(self, on_text: Callable[..., None] | None = None) -> None:
        self.on_text = on_text
        self._started: dict[str, float] = {}
        self._t0 = time.perf_counter()
        self.timings: dict[str, float] = {}  # seconds each finished stage took
        self.spans: dict[str, list[float]] = {}  # stage -> [start, seconds], from when the job started

    # the old interface: log("message", 0.4)
    def __call__(self, message: str, fraction: float | None = None) -> None:
        self.emit("message", text=message, fraction=fraction)

    def emit(self, type: str, **data) -> None:
        if self.on_text is not None:
            text = describe(type, data)
            if text:
                if type == "message" and data.get("fraction") is not None:
                    self.on_text(text, data["fraction"])
                else:
                    self.on_text(text)

    def stage(self, stage: str, status: str, detail: str = "") -> None:
        data: dict = {"stage": stage, "status": status}
        if detail:
            data["detail"] = detail
        if status == "running":
            self._started[stage] = time.perf_counter()
        elif stage in self._started:
            began = self._started.pop(stage)
            data["seconds"] = round(time.perf_counter() - began, 2)
            self.timings[stage] = data["seconds"]
            self.spans[stage] = [round(began - self._t0, 2), data["seconds"]]
        self.emit("stage", **data)

    def check_cancelled(self) -> None:
        """Raise Cancelled if the job was cancelled. The base reporter never is."""


def describe(type: str, data: dict) -> str:
    if type == "message":
        return data.get("text", "")
    if type == "stage":
        name = STAGE_NAMES.get(data["stage"], data["stage"])
        detail = f": {data['detail']}" if data.get("detail") else ""
        return {"running": f"{name}...", "done": f"{name} done{detail}", "failed": f"{name} failed{detail}",
                "skipped": ""}.get(data["status"], "")
    if type == "rejected":
        return f"The verifier sent {data['stage']} attempt {data['attempt']} back: {data['reason']}"
    if type == "clip":
        return ""  # the scene events already say it
    if type == "scene":
        verb = "Speaking" if data["stage"] == "voice" else "Drew"
        return f"{verb} {data['name']} ({data['index'] + 1}/{data['total']})"
    return ""


def reporter(log=None) -> Reporter:
    """A Reporter from whatever the caller passed: a Reporter, a plain function, or nothing (print)."""
    if isinstance(log, Reporter):
        return log
    return Reporter(log if log is not None else _print)


def _print(message: str, fraction: float | None = None) -> None:
    print(message)


def emit(log, type: str, **data) -> None:
    """Send a structured event through `log` whatever it is (used by the planner, quiz and reviser)."""
    reporter(log).emit(type, **data)
