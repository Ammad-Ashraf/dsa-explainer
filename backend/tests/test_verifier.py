import pytest
from dsa_explainer.core.lesson import Op
from dsa_explainer.core.verifier import fact_claims, stray_numbers, verify_lesson

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


# --- Milestone 7: declared claims, exact moments, counts, paraphrases ----------------------------

from dsa_explainer.core.lesson import Claim  # noqa: E402


def test_a_fact_true_only_before_the_step_is_caught():
    """Gap 1: "the root is 1" on the step that removes 1 used to pass, because it was true before the step."""
    lesson = load("min_heap")
    lesson.scenes[3].narration = ("Extract min removes the minimum. The root is 1, so 6 moves up to the root and sinks "
                                  "past its smaller child 3.")
    errors = verify_lesson(lesson).errors
    assert any("which was true before this step" in e and '"when": "before"' in e for e in errors), errors


def test_declaring_a_claim_as_before_makes_it_legal_and_checks_it_exactly():
    lesson = load("min_heap")
    lesson.scenes[3].narration = ("Extract min removes the minimum. The root is 1, so 6 moves up to the root and sinks "
                                  "past its smaller child 3.")
    lesson.scenes[3].claims = [Claim(fact="root", value=1, when="before")]
    assert verify_lesson(lesson).ok
    lesson.scenes[3].claims = [Claim(fact="root", value=1, when="after")]  # wrong moment
    assert any("claims the root is 1 right after the step, but it is 3" in e for e in verify_lesson(lesson).errors)


def test_a_declared_claim_must_be_said_and_must_name_a_real_fact():
    lesson = load("stack")
    lesson.scenes[2].claims = [Claim(fact="size", value=4)]
    lesson.scenes[2].narration = "We push another plate on top of the pile, and it waits there for the next pop."
    report = verify_lesson(lesson)
    assert any("never says 4" in e for e in report.errors), report.errors
    lesson.scenes[2].claims = [Claim(fact="height", value=4)]
    assert any("'height'" in e for e in verify_lesson(lesson).errors)


def test_a_wrong_count_is_no_longer_waved_through():
    """Gap 2: any number from 0 to 8 used to pass as a count; "D drops to 7" went unchecked."""
    lesson = load("dijkstra")
    lesson.scenes[3].narration = lesson.scenes[3].narration.replace("so D drops to 8", "so D drops to 7")
    errors = verify_lesson(lesson).errors
    assert any("distance of D is 7" in e for e in errors), errors
    lesson = load("stack")
    lesson.scenes[2].narration += " That took 6 tries."
    assert any("mentions 6" in e for e in verify_lesson(lesson).errors)


def test_counts_the_simulator_reports_may_be_mentioned():
    lesson = load("bubble_sort")
    lesson.scenes[1].narration += " The pass made 5 comparisons."
    assert verify_lesson(lesson).ok
    lesson.scenes[1].narration = lesson.scenes[1].narration.replace("5 comparisons", "11 comparisons")
    assert any("mentions 11" in e for e in verify_lesson(lesson).errors)


@pytest.mark.parametrize("text, claim", [
    ("The stack now holds 3 values.", ("size", "3")),
    ("It has four items left in it.", ("size", "4")),
    ("Only two nodes remain in the heap.", ("size", "2")),
    ("So 7 is now the top.", ("top", "7")),
    ("Plate 9 sits on top.", ("top", "9")),
    ("Now 5 becomes the new root.", ("root", "5")),
    ("The front changes to 8.", ("front", "8")),
    ("The distance to D drops to 7.", ("dist_D", "7")),
    ("D's distance is now 9.", ("dist_D", "9")),
    ("So D drops to 8.", ("dist_D", "8")),
    ("The distance of C is infinity.", ("dist_C", "inf")),
])
def test_paraphrased_claims_are_recognised(text, claim):
    assert claim in fact_claims(text, {"5", "7", "8", "9"})


@pytest.mark.parametrize("text", [
    "The top is where new plates go.",
    "This is the root of the problem.",
    "A queue has many uses in practice.",
    "It is the front that matters.",
])
def test_ordinary_sentences_are_not_claims(text):
    assert fact_claims(text, set()) == []
