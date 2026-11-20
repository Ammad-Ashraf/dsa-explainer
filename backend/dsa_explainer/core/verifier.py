"""Step verifier. Runs every step of a plan on the real data structure and
checks three things:

1. the operation is possible (no pop on an empty stack),
2. the planner's claimed_state equals the true state after the step,
3. every claim the scene declares ({"fact": "root", "value": 3, "when":
   "before"}) is exactly true at that moment, and the narration says it,
4. the narration does not contradict the true state: any "top is 7" /
   "7 is at the front" / "holds 3 values" claim it makes must be true right
   after the step (or before it, when a declared claim says so), and every
   number it mentions must be a value, an argument or one of the simulator's
   own counts at that moment.

Quiz answers are checked the same way: the question's operations are run and
the asked fact is compared with the given answer. A plan with any error is
sent back to the planner; nothing is rendered until it passes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .. import algorithms
from ..algorithms import MAX_ITEMS, OpError, build, fact_text, normalize
from .lesson import Lesson, Question, Scene, scene_labels

MIN_WORDS = 90  # about 36 s of speech: the video must last at least 30 s
MIN_STEPS, MAX_STEPS = 3, 10


@dataclass
class Frame:
    """What the renderer needs for one scene: the true picture before and after."""

    before: dict
    after: dict
    focus: list
    state: object  # plain state after the scene (shown to the reviser)
    lines: list = field(default_factory=list)  # pseudocode lines the step's operation ran (from the simulator)
    strip_before: list = field(default_factory=list)  # the facts strip before and after the scene
    strip_after: list = field(default_factory=list)


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
_VERB = (r"(?:is now|now is|is|becomes|will be|remains|stays|now points to|points to|drops to|falls to|rises to|"
         r"grows to|shrinks to|goes up to|goes down to|changes to|is updated to|is set to|is lowered to|equals)")
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
# "7 is now the top", "B becomes the new root"
_CLAIM_C = re.compile(rf"\b([A-Za-z0-9-]+)\s+(?:is now|now is|becomes|is)\s+(?:now\s+)?the\s+(?:new\s+)?{_FACT}\b"
                      rf"(?!\s+(?:of|to)\b)", re.IGNORECASE)
_NOUNS = r"(?:values?|items?|nodes?|keys?|numbers?|elements?|plates?|jobs?|entries|cells?)"
# "the stack now holds 3 values", "it has four items", "3 values are left"
_SIZE_A = re.compile(rf"\b(?:holds|has|contains|keeps|stores)\s+(?:only\s+|just\s+|exactly\s+)?"
                     rf"([A-Za-z0-9]+)\s+{_NOUNS}\b", re.IGNORECASE)
_SIZE_B = re.compile(rf"\b([A-Za-z0-9]+)\s+{_NOUNS}\s+(?:remain|are left|are still in)\b", re.IGNORECASE)
# Dijkstra: "the distance to D drops to 7", "D's distance is 7", "D drops to 7"
_DIST_A = re.compile(rf"\bdistance\s+(?:of|to|for)\s+(?:node\s+)?([A-Z])\b\s+{_VERB}\s+(?:now\s+)?([0-9]+|infinity)",
                     re.IGNORECASE)
_DIST_B = re.compile(rf"\b([A-Z])'s\s+distance\s+{_VERB}\s+(?:now\s+)?([0-9]+|infinity)")
_DIST_C = re.compile(r"\b([A-Z])\s+(?:drops|falls|improves|goes down)\s+to\s+([0-9]+)\b")
# counts the simulator keeps: "after only three comparisons", "that is 4 swaps"
_COUNT = re.compile(r"([A-Za-z0-9]+)\s+(comparisons|swaps|shifts)", re.IGNORECASE)
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
    found += [(m.group(2), m.group(1)) for m in _CLAIM_C.finditer(text)]
    found += [("size", m.group(1)) for r in (_SIZE_A, _SIZE_B) for m in r.finditer(text)]
    found += [(m.group(2).lower(), m.group(1)) for m in _COUNT.finditer(text)]
    claims = []
    for r in (_DIST_A, _DIST_B, _DIST_C):
        for m in r.finditer(text):
            said = m.group(2).lower()
            claims.append((f"dist_{m.group(1).upper()}", "inf" if said == "infinity" else said))
    for word, said in found:
        key = re.sub(r"\s+", " ", word.lower())
        fact = _FACT_WORDS.get(key, key)  # size and the counts name their fact directly
        said = said.lower()
        said = _NUMBER_WORDS.get(said, said)
        if said in _EMPTY_WORDS:
            said = "empty"
        elif fact in ("size", "comparisons", "swaps", "shifts"):
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


def check_narration(label: str, text: str, facts_list: list[dict], allowed: set[str],
                    before: dict | None = None) -> tuple[list[str], int]:
    """Errors in one narration, and how many claims were checked. A claim must be true in one of `facts_list`
    (for a step: the state right after it, plus the facts it declared as true before it); `before` is only
    used to explain an error."""
    errors, checks = [], 0
    for fact, said in fact_claims(text, allowed):
        truths = {_text(f[fact]) for f in facts_list if fact in f}
        if not truths:
            continue  # e.g. "top" in a queue lesson: nothing to compare with
        checks += 1
        if normalize(said) in truths:
            continue
        name = fact.replace("dist_", "distance of ").replace("_", " ")
        if before is not None and fact in before and _text(before[fact]) == normalize(said):
            errors.append(f"{label}: the narration says the {name} is {said}, which was true before this step; "
                          f"right after it the {name} is {' or '.join(sorted(truths))}. Say it in the past tense, or "
                          f'declare it in "claims" with "when": "before".')
        else:
            errors.append(f'{label}: the narration says the {name} is {said}, but it is {" or ".join(sorted(truths))}.')
    for n in stray_numbers(text, allowed):
        errors.append(f"{label}: the narration mentions {n}, which is not a value, an argument or a count "
                      f"of the structure at this point.")
    return errors, checks + 1


def _text(value) -> str:
    return normalize(fact_text(value))


def numbers_in(facts: dict) -> set[str]:
    """The counts and indices a narration may mention: every whole number among the simulator's facts."""
    out = set()
    for value in facts.values():
        for v in value if isinstance(value, (list, tuple)) else [value]:
            if isinstance(v, int) and not isinstance(v, bool):
                out.add(str(v))
    return out


def check_claims(label: str, scene: Scene, before: dict, after: dict) -> tuple[list[str], int]:
    """Each declared claim must be exactly true at its moment, and the narration must say it."""
    errors = []
    words = {normalize(w) for w in re.findall(r"[A-Za-z0-9-]+", scene.narration)}
    words |= {_NUMBER_WORDS[w] for w in words if w in _NUMBER_WORDS}
    for claim in scene.claims:
        facts = before if claim.when == "before" else after
        if claim.fact not in facts:
            errors.append(f"{label}: claims the fact '{claim.fact}', which this structure does not have; "
                          f"use one of: {', '.join(sorted(facts))}.")
            continue
        truth, said = _text(facts[claim.fact]), _text(claim.value)
        if re.sub(r"\s", "", truth) != re.sub(r"\s", "", said):
            moment = "just before" if claim.when == "before" else "right after"
            errors.append(f"{label}: claims the {claim.fact} is {said} {moment} the step, but it is {truth}.")
            continue
        missing = [t for t in re.split(r"[,\s]+", said) if t and t not in words]
        if missing:
            errors.append(f"{label}: claims the {claim.fact} is {said}, but the narration never says "
                          f"{', '.join(missing)}.")
    return errors, len(scene.claims)


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
    value = fact_text(facts[q.ask])
    if q.claim is not None:  # a true/false question
        return "True" if _same(value, str(q.claim)) else "False"
    return value


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
    if q.claim is not None and sorted(o.lower() for o in q.options) != ["false", "true"]:
        return 'a true/false question (one with a "claim") must have exactly the options True and False'
    for option in q.why_wrong:
        if option not in q.options or _same(option, truth):
            return f"why_wrong explains '{option}', which is not a wrong option"
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

    every_arg = set().union(*(_arg_values(s.op) for s in lesson.scenes))
    first = ds.facts()
    seen_facts, seen_values = [first], ds.values() | every_arg | numbers_in(first)

    for label, scene in zip(scene_labels(lesson), lesson.scenes):
        before, facts_before, values_before, strip_before = ds.snapshot(), ds.facts(), ds.values(), ds.strip()
        focus: list = []
        lines: list = []
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
            lines = ds.code_lines(scene.op.name)
            if scene.claimed_state is None:
                err.append(f"{label}: claimed_state is missing.")
            elif not ds.matches(scene.claimed_state):
                err.append(
                    f"{label} ({scene.op.describe()}): claimed_state {_compact(scene.claimed_state)} is wrong; "
                    f"the real state after this step is {_compact(ds.state())}."
                )
            report.checks += 1
            facts_after = ds.facts()
            declared_before = {c.fact for c in scene.claims if c.when == "before"}
            facts_ok = [facts_after, {f: v for f, v in facts_before.items() if f in declared_before}]
            allowed = (values_before | ds.values() | _arg_values(scene.op) | numbers_in(facts_before)
                       | numbers_in(facts_after))
            seen_facts.append(facts_after)
            seen_values |= ds.values() | numbers_in(facts_after)
        else:
            if scene.op is not None:
                err.append(f"{label}: only step scenes may have an op.")
            if scene.kind == "intro":
                facts_ok, allowed = [facts_before], values_before | every_arg | numbers_in(facts_before)
            else:  # summary: may recall anything that happened
                facts_ok, allowed = seen_facts, seen_values
        claims_before = facts_before if scene.kind == "step" else (first if scene.kind == "summary" else facts_before)
        problems, checks = check_claims(label, scene, claims_before, ds.facts())
        err.extend(problems)
        report.checks += checks
        problems, checks = check_narration(label, scene.narration, facts_ok, allowed,
                                           facts_before if scene.kind == "step" else None)
        err.extend(problems)
        report.checks += checks
        report.frames.append(Frame(before, ds.snapshot(), focus, ds.state(), lines, strip_before, ds.strip()))

    for i, q in enumerate(lesson.quiz, 1):
        problem = check_question(lesson, q)
        report.checks += 1
        if problem:
            err.append(f"quiz question {i}: {problem}")
    return report


def _compact(x) -> str:
    return json.dumps(x, separators=(", ", ": "))
