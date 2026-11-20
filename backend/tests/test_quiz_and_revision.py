import json

import pytest

from dsa_explainer.authoring import quiz, revise
from dsa_explainer.core.lesson import Question
from dsa_explainer.core.verifier import check_question, verify_lesson

from .helpers import EXAMPLES, fake_llm, load, raw


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


# --- Milestone 7: simulated mistakes, true/false questions, repaired options ----------------------

from dsa_explainer.authoring import mistakes  # noqa: E402
from dsa_explainer.core.lesson import Op  # noqa: E402
from dsa_explainer.core.verifier import question_answer  # noqa: E402


def test_mistakes_are_simulated_and_all_wrong():
    lesson = load("queue")
    # [3, 8] -> enqueue 5 -> [3, 8, 5] -> dequeue -> [8, 5]: the front is 8
    q = Question(question="?", start=[3, 8], ops=[Op(name="enqueue", args={"value": 5}), Op(name="dequeue")],
                 ask="front", options=["8", "3"], answer="8")
    # the wrong order ([8] then [8, 5]) and treating it as a stack (top 8) both give 8, the true answer: dropped
    assert mistakes.mistakes(lesson, q) == {"3": "forgetting the last operation",
                                            "5": "running the last operation twice"}
    stack = load("stack")  # [4, 9, 2] -> push 7 -> pop: a queue would pop 4 from the other end
    q = Question(question="?", start=[4, 9], ops=[Op(name="push", args={"value": 7}), Op(name="pop")], ask="top",
                 options=["9", "7"], answer="9")
    assert mistakes.mistakes(stack, q)["7"] in ("forgetting the last operation", "treating the stack as a queue")


@pytest.mark.parametrize("name", EXAMPLES)
def test_builtin_questions_verify_for_every_lesson(name):
    lesson = load(name)
    questions = quiz.builtin_questions(lesson, 3)
    assert len(questions) >= 2
    for q in questions:
        assert check_question(lesson, q) is None
        truth = question_answer(lesson, q)
        for option, why in q.why_wrong.items():  # every explained option is really wrong, by that mistake
            assert option in q.options and option.lower() != truth.lower() and why


def test_true_false_questions_are_checked_by_running():
    lesson = load("stack")
    q = Question(question="True or false: after pushing 7 the top is 7.", ops=[Op(name="push", args={"value": 7})],
                 ask="top", options=["True", "False"], answer="True", claim="7")
    assert check_question(lesson, q) is None
    q.answer = "False"
    assert "wrong" in check_question(lesson, q)
    q.answer, q.options = "True", ["True", "False", "Maybe"]
    assert check_question(lesson, q) is not None


def test_a_right_answer_with_broken_options_is_repaired_not_thrown_away():
    lesson = load("stack")
    ops = [Op(name="push", args={"value": 7}), Op(name="pop")]
    broken = Question(question="Push 7, then pop. What is the top?", ops=ops, ask="top", options=["4", "4", "7"],
                      answer="9")  # right, but missing from the options, and two options alike
    assert check_question(lesson, broken) is not None
    fixed = quiz.repair(lesson, broken)
    assert check_question(lesson, fixed) is None and "9" in fixed.options and "4" in fixed.options
    assert fixed.why_wrong.get("7") == "forgetting the last operation"


def test_a_wrong_answer_is_not_repaired():
    lesson = load("stack")
    q = Question(question="Push 7. What is the top?", ops=[Op(name="push", args={"value": 7})], ask="top",
                 options=["2", "7"], answer="2")
    assert quiz.repair(lesson, q).answer == "2" and check_question(lesson, quiz.repair(lesson, q)) is not None


def test_why_wrong_may_not_explain_the_right_answer():
    lesson = load("stack")
    q = Question(question="Push 7. What is the top?", ops=[Op(name="push", args={"value": 7})], ask="top",
                 options=["2", "7"], answer="7", why_wrong={"7": "nonsense"})
    assert "not a wrong option" in check_question(lesson, q)
