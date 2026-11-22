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


def fake_build(lesson, report, out, quality, rep, quiz=None):
    if quiz is not None:
        lesson.quiz = quiz.result()
    out.write_bytes(b"\x00")
    return {"video": out, "seconds": 3.0, "clips": 1, "rendered": ["intro"], "reused": 0, "voice_seconds": 1.0,
            "build_seconds": 2.0, "clip_keys": [], "chapters": []}


def test_a_quiz_failure_keeps_the_verified_lesson(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path)
    lesson = load("stack")
    lesson.quiz = []
    monkeypatch.setattr(planner, "plan_lesson", lambda topic, level, log, structure=None: (lesson, []))

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


def test_the_quiz_is_written_while_the_video_is_built(tmp_path, monkeypatch):
    """Milestone 8: a slow quiz call overlaps the voice and drawing instead of adding its time to the wait."""
    import threading
    import time

    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path)
    lesson = load("stack")
    questions = list(lesson.quiz)
    lesson.quiz = []
    monkeypatch.setattr(planner, "plan_lesson", lambda topic, level, log, structure=None: (lesson, []))
    quiz_started, seen = threading.Event(), {}

    def slow_quiz(lesson, log=None):
        quiz_started.set()
        time.sleep(0.6)  # a language model thinking
        return questions

    def build(lesson, report, out, quality, rep, quiz=None):
        seen["at"], seen["quiz_done"] = time.perf_counter(), quiz.done()
        return fake_build(lesson, report, out, quality, rep, quiz)

    monkeypatch.setattr(quiz, "make_quiz", slow_quiz)
    monkeypatch.setattr(video, "build_video", build)
    started = time.perf_counter()
    result = pipeline.make_lesson("how does a stack work", "beginner", "draft", Recorder())
    assert quiz_started.is_set() and seen["quiz_done"] is False  # the build did not wait for the quiz
    assert seen["at"] - started < 0.5
    assert [q.question for q in result["lesson"].quiz] == [q.question for q in questions]
    meta, _ = store.get(result["lesson_id"])
    stages = meta["versions"][0]["timings"]["stages"]
    assert {"plan", "verify", "quiz"} <= set(stages) and stages["quiz"] >= 0.5
