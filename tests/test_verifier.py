import pytest

from dsa_explainer.lesson import Op
from dsa_explainer.verifier import fact_claims, stray_numbers, verify_lesson

from .helpers import EXAMPLES, load


@pytest.mark.parametrize("name", EXAMPLES)
def test_every_example_lesson_verifies(name):
    lesson = load(name)
    report = verify_lesson(lesson)
    assert report.ok, report.errors
    assert len(report.frames) == len(lesson.scenes)


def test_wrong_claimed_state_is_caught():
    lesson = load("stack")
    lesson.scenes[2].claimed_state = [4, 9, 7]  # forgot the 2
    errors = verify_lesson(lesson).errors
    assert len(errors) == 1 and "[4, 9, 2, 7]" in errors[0]


def test_false_fact_in_narration_is_caught():
    lesson = load("stack")
    lesson.scenes[4].narration = lesson.scenes[4].narration.replace("The top is now 2", "The top is now 9")
    assert any("says the top is 9" in e for e in verify_lesson(lesson).errors)


def test_invented_number_is_caught():
    lesson = load("queue")
    lesson.scenes[1].narration = "Job 42 arrives, so we enqueue it at the rear, where new jobs always wait their turn."
    assert any("mentions 42" in e for e in verify_lesson(lesson).errors)


def test_impossible_operation_is_caught():
    lesson = load("stack")
    for scene in lesson.scenes[1:7]:
        scene.op = Op(name="pop")
    errors = verify_lesson(lesson).errors
    assert any("cannot pop" in e for e in errors)


def test_wrong_quiz_answer_is_caught():
    lesson = load("bst")
    lesson.quiz[0].answer = "3"
    assert any("quiz question 1" in e and "'10'" in e for e in verify_lesson(lesson).errors)


def test_too_short_lesson_is_caught():
    lesson = load("stack")
    for scene in lesson.scenes:
        scene.narration = "Short words here."
    assert any("at least" in e for e in verify_lesson(lesson).errors)


def test_fact_claim_patterns():
    assert fact_claims("Now the top of the stack is 7.", set()) == [("top", "7")]
    assert fact_claims("So 5 is now at the front.", set()) == [("front", "5")]
    assert fact_claims("The size is three.", set()) == [("size", "3")]
    assert fact_claims("The current node is B.", {"b"}) == [("current", "b")]
    assert fact_claims("The top is where new plates go.", set()) == []


def test_stray_numbers_ignore_big_o_and_step_numbers():
    assert stray_numbers("Step 9 runs in O(1) time and adds 7.", {"7"}) == []
    assert stray_numbers("We push 12.", {"7"}) == ["12"]
