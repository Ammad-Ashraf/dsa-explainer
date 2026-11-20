"""Step verifier. Runs every step of a plan on the real data structure and
checks three things:

1. the operation is possible (no pop on an empty stack),
2. the planner's claimed_state equals the true state after the step,
3. the narration does not contradict the true state: any "top is 7" /
   "7 is at the front" / "size is 3" claim must be true, and every number it
   mentions must exist in the structure or the operation.

Quiz answers are checked the same way: the question's operations are run and
the asked fact is compared with the given answer. A plan with any error is
sent back to the planner; nothing is rendered until it passes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .lesson import Lesson, Question, scene_labels
from .. import algorithms
from ..algorithms import MAX_ITEMS, OpError, build, fact_text, normalize

MIN_WORDS = 90  # about 36 s of speech: the video must last at least 30 s
MIN_STEPS, MAX_STEPS = 3, 10


@dataclass
class Frame:
    """What the renderer needs for one scene: the true picture before and after."""

    before: dict
    after: dict
    focus: list
    state: object  # plain state after the scene (shown to the reviser)


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    checks: int = 0
    frames: list[Frame] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


# --- narration checks -----------------------------------------------------------

_FACT_WORDS = algorithms.fact_words()  # shared words (top, front, root, size...) plus each algorithm's own
_FACT = "(" + "|".join(sorted((w.replace(" ", r"\s+") for w in _FACT_WORDS), key=len, reverse=True)) + ")"
_VERB = r"(?:is now|now is|is|becomes|will be|remains|stays|now points to|points to)"
# "the top of the stack is now 7", "the size is 3", "head now points to 5"
_CLAIM_A = re.compile(
    rf"\b{_FACT}(?:\s+(?:element|item|node|value|pointer))?(?:\s+of\s+the\s+[a-z]+(?:\s+[a-z]+)?)?"
    rf"\s+{_VERB}\s+(?:now\s+)?(?:the\s+)?(?:value\s+|node\s+|number\s+)?([A-Za-z0-9-]+)",
    re.IGNORECASE,
)
# "7 is now on top", "5 is at the front"
_CLAIM_B = re.compile(
    rf"\b([A-Za-z0-9-]+)\s+(?:is now|now is|is|becomes|sits|stays)\s+(?:now\s+)?(?:on|at)\s+(?:the\s+)?{_FACT}\b",
    re.IGNORECASE,
)
_NUMBER_WORDS = {w: str(i) for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve".split())}
_EMPTY_WORDS = {"empty", "null", "none", "nothing"}

_BIG_O = re.compile(r"\bO\s*\([^)]*\)")
_COUNTED = re.compile(r"\b(?:step|scene|question|part|level)\s+\d+\b", re.IGNORECASE)
_NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?!\w)")


def fact_claims(text: str, known: set[str]) -> list[tuple[str, str]]:
    """(fact, value) pairs the narration states, e.g. ("top", "7").
    Words that are not values ("the top is where...") are ignored."""
    found = [(m.group(1), m.group(2)) for m in _CLAIM_A.finditer(text)]
    found += [(m.group(2), m.group(1)) for m in _CLAIM_B.finditer(text)]
    claims = []
    for word, said in found:
        fact = _FACT_WORDS[re.sub(r"\s+", " ", word.lower())]
        said = said.lower()
        said = _NUMBER_WORDS.get(said, said)
        if said in _EMPTY_WORDS:
            said = "empty"
        elif fact == "size":
            if not said.isdigit():
                continue
        elif not (said.lstrip("-").isdigit() or said in known):
            continue
        claims.append((fact, said))
    return claims


def stray_numbers(text: str, allowed: set[str]) -> list[str]:
    """Numbers in the narration that are neither in the structure nor the operation."""
    text = _COUNTED.sub(" ", _BIG_O.sub(" ", text))
    return sorted({n for n in _NUMBER.findall(text) if normalize(n) not in allowed})


def check_narration(label: str, text: str, facts_list: list[dict], allowed: set[str]) -> tuple[list[str], int]:
    """Errors in one narration, and how many claims were checked."""
    errors, checks = [], 0
    for fact, said in fact_claims(text, allowed):
        truths = {normalize(fact_text(f[fact])) for f in facts_list if fact in f}
        if not truths:
            continue  # e.g. "top" in a queue lesson: nothing to compare with
        checks += 1
        if normalize(said) not in truths:
            errors.append(f'{label}: the narration says the {fact} is {said}, but it is {" or ".join(sorted(truths))}.')
    for n in stray_numbers(text, allowed):
        errors.append(f"{label}: the narration mentions {n}, which is not in the structure or this step's operation.")
    return errors, checks + 1


def _arg_values(op) -> set[str]:
    return {normalize(v) for v in op.args.values()} if op else set()


# --- quiz checks ----------------------------------------------------------------


def question_answer(lesson: Lesson, q: Question) -> str:
    """The true answer to a question, computed by running its operations."""
    ds = build(lesson.structure, q.start if q.start is not None else lesson.initial)
    for op in q.ops:
        ds.run(op.name, op.args)
    facts = ds.facts()
    if q.ask not in facts:
        raise OpError(f"ask must be one of: {', '.join(facts)}")
    return fact_text(facts[q.ask])


def _same(a: str, b: str) -> bool:
    return re.sub(r"[\s\[\]'\"]", "", a).lower() == re.sub(r"[\s\[\]'\"]", "", b).lower()


def check_question(lesson: Lesson, q: Question) -> str | None:
    """None if the question is correct, otherwise what is wrong with it."""
    try:
        truth = question_answer(lesson, q)
    except OpError as exc:
        return f"its operations cannot run: {exc}"
    if not _same(q.answer, truth):
        return f"the answer '{q.answer}' is wrong; running the operations gives {q.ask} = '{truth}'"
    if sum(_same(o, truth) for o in q.options) != 1:
        return f"exactly one option must be the correct answer '{truth}'"
    if len({re.sub(r'\s', '', o.lower()) for o in q.options}) != len(q.options):
        return "the options must all be different"
    allowed = {normalize(v) for v in re.findall(r"-?\d+", q.question + " " + " ".join(q.options))}
    allowed |= {str(i) for i in range(MAX_ITEMS + 2)}
    stray = stray_numbers(q.explanation, allowed)
    if stray:
        return f"the explanation mentions {', '.join(stray)}, which is not in the question"
    return None


def answer_index(lesson: Lesson, q: Question) -> int:
    truth = question_answer(lesson, q)
    return next(i for i, o in enumerate(q.options) if _same(o, truth))


# --- the whole lesson -------------------------------------------------------------


def verify_lesson(lesson: Lesson) -> Report:
    report = Report()
    err = report.errors
    kinds = [s.kind for s in lesson.scenes]
    if not kinds or kinds[0] != "intro" or kinds[-1] != "summary" or kinds.count("intro") + kinds.count("summary") != 2:
        err.append("The plan must start with one intro scene and end with one summary scene.")
    steps = kinds.count("step")
    if not MIN_STEPS <= steps <= MAX_STEPS:
        err.append(f"Use {MIN_STEPS} to {MAX_STEPS} step scenes (found {steps}).")
    words = sum(len(s.narration.split()) for s in lesson.scenes)
    if words < MIN_WORDS:
        err.append(f"The narration has {words} words; write at least {MIN_WORDS} so the video lasts over 30 seconds.")

    try:
        ds = build(lesson.structure, lesson.initial)
    except OpError as exc:
        err.append(f"initial: {exc}")
        return report

    counts = {str(i) for i in range(MAX_ITEMS + 2)}
    every_arg = set().union(*(_arg_values(s.op) for s in lesson.scenes))
    seen_facts, seen_values = [ds.facts()], ds.values() | every_arg | counts

    for label, scene in zip(scene_labels(lesson), lesson.scenes):
        before, facts_before, values_before = ds.snapshot(), ds.facts(), ds.values()
        focus: list = []
        if scene.kind == "step":
            if scene.op is None:
                err.append(f"{label}: a step scene needs an op.")
                break
            try:
                focus = ds.run(scene.op.name, scene.op.args)
            except OpError as exc:
                err.append(f"{label} ({scene.op.describe()}): {exc}")
                break  # later states would be meaningless
            report.checks += 1
            if scene.claimed_state is None:
                err.append(f"{label}: claimed_state is missing.")
            elif not ds.matches(scene.claimed_state):
                err.append(
                    f"{label} ({scene.op.describe()}): claimed_state {_compact(scene.claimed_state)} is wrong; "
                    f"the real state after this step is {_compact(ds.state())}."
                )
            report.checks += 1
            facts_ok = [facts_before, ds.facts()]
            allowed = values_before | ds.values() | _arg_values(scene.op) | counts
            seen_facts.append(ds.facts())
            seen_values |= ds.values()
        else:
            if scene.op is not None:
                err.append(f"{label}: only step scenes may have an op.")
            if scene.kind == "intro":
                facts_ok, allowed = [facts_before], values_before | every_arg | counts
            else:  # summary: may recall anything that happened
                facts_ok, allowed = seen_facts, seen_values
        problems, checks = check_narration(label, scene.narration, facts_ok, allowed)
        err.extend(problems)
        report.checks += checks
        report.frames.append(Frame(before, ds.snapshot(), focus, ds.state()))

    for i, q in enumerate(lesson.quiz, 1):
        problem = check_question(lesson, q)
        report.checks += 1
        if problem:
            err.append(f"quiz question {i}: {problem}")
    return report


def _compact(x) -> str:
    return json.dumps(x, separators=(", ", ": "))
