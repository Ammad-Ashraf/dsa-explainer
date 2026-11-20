"""Background jobs: making, rendering and revising lessons.

One worker thread runs jobs in order (drawing is CPU-bound and the voice engine
is not thread-safe). Each job keeps every event it reported, so a page that
connects late can replay the whole history, then follow new events live.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from typing import Callable

from .. import events

log = logging.getLogger("dsa_explainer.jobs")
KEEP_FINISHED = 50  # finished jobs remembered for late listeners
FINAL = ("done", "failed", "cancelled")


@dataclass
class Job:
    kind: str
    params: dict
    run: Callable[["JobReporter"], dict]
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: str = "queued"  # queued | running | done | failed | cancelled
    created: float = field(default_factory=time.time)
    started: float | None = None
    finished: float | None = None
    result: dict | None = None
    error: str | None = None
    cancel_requested: bool = False
    events: list[dict] = field(default_factory=list)
    stages: dict[str, dict] = field(default_factory=dict)
    fraction: float = 0.0
    message: str = ""
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add_event(self, type: str, data: dict) -> None:
        with self._lock:
            event = {"seq": len(self.events), "type": type, "time": round(time.time(), 3), **data}
            self.events.append(event)
            if type == "stage":
                self.stages[data["stage"]] = {k: v for k, v in data.items() if k != "stage"}
            elif type == "message":
                self.message = data.get("text", "")
                if data.get("fraction") is not None:
                    self.fraction = max(self.fraction, float(data["fraction"]))

    def events_since(self, seq: int) -> list[dict]:
        with self._lock:
            return self.events[seq:]

    @property
    def finished_state(self) -> bool:
        return self.status in FINAL

    def snapshot(self, with_events: bool = False) -> dict:
        with self._lock:
            out = {
                "id": self.id, "kind": self.kind, "params": self.params, "status": self.status,
                "created": self.created, "started": self.started, "finished": self.finished,
                "result": self.result, "error": self.error, "stages": dict(self.stages),
                "fraction": self.fraction, "message": self.message, "events": len(self.events),
            }
            if with_events:
                out["event_log"] = list(self.events)
            return out


class JobReporter(events.Reporter):
    """Stores every pipeline event on its job, and stops the job when it is cancelled."""

    def __init__(self, job: Job) -> None:
        super().__init__(None)
        self.job = job

    def emit(self, type: str, **data) -> None:
        self.job.add_event(type, data)
        if type in ("message", "scene"):
            self.check_cancelled()

    def check_cancelled(self) -> None:
        if self.job.cancel_requested:
            raise events.Cancelled("Cancelled.")


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._queue: queue.Queue[Job] = queue.Queue()
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._work, name="dsa-jobs", daemon=True)
        self._worker.start()

    def submit(self, kind: str, params: dict, run: Callable[[JobReporter], dict]) -> Job:
        job = Job(kind=kind, params=params, run=run)
        job.add_event("job", {"status": "queued", "position": self._queue.qsize()})
        with self._lock:
            self._jobs[job.id] = job
            self._forget_old()
        self._queue.put(job)
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> list[Job]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created, reverse=True)

    def cancel(self, job_id: str) -> Job | None:
        job = self.get(job_id)
        if job and not job.finished_state:
            job.cancel_requested = True
            if job.status == "queued":
                self._finish(job, "cancelled", error="Cancelled before it started.")
        return job

    def _forget_old(self) -> None:
        done = sorted((j for j in self._jobs.values() if j.finished_state), key=lambda j: j.created)
        for job in done[: max(0, len(done) - KEEP_FINISHED)]:
            del self._jobs[job.id]

    def _finish(self, job: Job, status: str, result: dict | None = None, error: str | None = None) -> None:
        job.result, job.error, job.finished = result, error, time.time()
        job.status = status
        job.add_event("job", {"status": status, "result": result, "error": error})

    def _work(self) -> None:
        while True:
            job = self._queue.get()
            if job.finished_state:  # cancelled while queued
                continue
            job.status, job.started = "running", time.time()
            job.add_event("job", {"status": "running"})
            try:
                result = job.run(JobReporter(job))
            except events.Cancelled:
                self._finish(job, "cancelled", error="Cancelled.")
            except Exception as exc:  # reported to the page; the traceback goes to the console
                log.error("job %s failed:\n%s", job.id, traceback.format_exc())
                for stage, state in job.stages.items():
                    if state.get("status") == "running":
                        job.add_event("stage", {"stage": stage, "status": "failed", "detail": str(exc)[:300]})
                self._finish(job, "failed", error=str(exc) or exc.__class__.__name__)
            else:
                self._finish(job, "done", result=result)
