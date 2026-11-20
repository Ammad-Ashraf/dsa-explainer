"""The whole pipeline with the language model and the renderer replaced: resilience and bookkeeping."""

from dsa_explainer import config, events, pipeline, store
from dsa_explainer.authoring import llm, planner, quiz
from dsa_explainer.media import video

from .helpers import load


class Recorder(events.Reporter):
    def __init__(self):
        super().__init__(None)
        self.events = []

    def emit(self, type, **data):
        self.events.append((type, data))


def fake_build(lesson, report, out, quality, rep):
    out.write_bytes(b"\x00")
    return {"video": out, "seconds": 3.0, "clips": 1, "rendered": ["intro"], "reused": 0, "voice_seconds": 1.0,
            "build_seconds": 2.0, "clip_keys": [], "chapters": []}


def test_a_quiz_failure_keeps_the_verified_lesson(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path)
    lesson = load("stack")
    lesson.quiz = []
    monkeypatch.setattr(planner, "plan_lesson", lambda topic, level, log: (lesson, []))

    def broken_quiz(lesson, log=None):
        raise llm.LLMError("Request timed out.")

    monkeypatch.setattr(quiz, "make_quiz", broken_quiz)
    monkeypatch.setattr(video, "build_video", fake_build)
    rep = Recorder()
    result = pipeline.make_lesson("how does a stack work", "beginner", "draft", rep)
    assert len(result["lesson"].quiz) == 2  # the built-in questions
    quiz_done = [d for t, d in rep.events if t == "stage" and d["stage"] == "quiz" and d["status"] == "done"]
    assert quiz_done and "built-in question" in quiz_done[0]["detail"]
    meta, _ = store.get(result["lesson_id"])
    assert meta["versions"][0]["checks"] > 0
