import json

import pytest

from dsa_explainer.authoring import quiz, revise
from dsa_explainer.core.lesson import Question
from dsa_explainer.core.verifier import check_question, verify_lesson

from .helpers import fake_llm, load, raw


def quiet(*_):
    pass


def test_quiz_answers_are_checked_by_running_the_operations():
    lesson = load("queue")
    q = Question(question="Queue 3, 8. Enqueue 5, dequeue. Front?", start=[3, 8],
                 ops=[{"name": "enqueue", "args": {"value": 5}}, {"name": "dequeue"}],
                 ask="front", options=["3", "8", "5"], answer="8")
    assert check_question(lesson, q) is None
    q.answer = "3"
    assert "wrong" in check_question(lesson, q)


def test_wrong_quiz_question_is_repaired(monkeypatch):
    lesson = load("stack")
    lesson.quiz = []
    good = raw("stack")["quiz"]
    bad = json.loads(json.dumps(good))
    bad[0]["answer"] = "5"
    fake_llm(monkeypatch, [json.dumps({"questions": bad}), json.dumps({"questions": good})])
    questions = quiz.make_quiz(lesson, n=2, log=quiet)
    assert [q.answer for q in questions] == ["8", "3"]


def test_fallback_question_is_correct():
    for name in ("stack", "bst", "bfs"):
        lesson = load(name)
        assert check_question(lesson, quiz.fallback_question(lesson)) is None


def test_slow_down_changes_only_that_step():
    lesson = load("stack")
    new, changed = revise.revise(lesson, "slow down step 4", log=quiet)
    assert changed == ["step 4"]
    assert new.scenes[4].speed == 0.75
    assert [s.speed for i, s in enumerate(new.scenes) if i != 4] == [1.0] * (len(new.scenes) - 1)


def test_unknown_step_is_refused():
    with pytest.raises(revise.RevisionError, match="no step 42"):
        revise.revise(load("stack"), "slow down step 42", log=quiet)


def test_rewrite_keeps_facts_true(monkeypatch):
    lesson = load("stack")
    wrong = {"changes": [{"scene": "step 2", "narration": "We push 7 onto the stack. The top is now 9, the oldest one."}]}
    right = {"changes": [{"scene": "step 2", "narration": "Imagine adding one more plate to the pile. We push 7 "
                                                          "and it sits on the very top. The top is now 7."}]}
    calls = fake_llm(monkeypatch, [json.dumps(wrong), json.dumps(right)])
    new, changed = revise.revise(lesson, "explain step 2 for a beginner", log=quiet)
    assert changed == ["step 2"]
    assert "says the top is 9" in calls[1][-1]["content"]  # the false fact was sent back
    assert verify_lesson(new).ok
