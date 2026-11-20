"""Mutation testing of the verifier: plant one mistake in a correct plan and see whether it is caught.

Each operator below plants one kind of mistake a language model makes (a wrong
predicted state, a wrong fact in the narration, an invented number, a changed
argument, a dropped or reordered step, a wrong quiz answer, ...). A mutant is
*caught* when verify_lesson reports an error. Some mutants are harmless by
chance (changing "4 swaps" to "5 swaps" where 5 is also a value on screen);
those survive and the report shows them, operator by operator, so the
remaining blind spots are visible. Used by tests/test_mutations.py and
scripts/mutation_report.py.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from .lesson import Lesson
from .verifier import fact_claims, verify_lesson

OUTSIDE = 97  # a number no saved plan uses


@dataclass
class Mutant:
    operator: str
    where: str
    lesson: Lesson


def _bump(x):
    """The first whole number in a JSON value, changed by one (None if there is none)."""
    if isinstance(x, bool):
        return None
    if isinstance(x, int):
        return x + 1
    if isinstance(x, list):
        for i, v in enumerate(x):
            new = _bump(v)
            if new is not None:
                return x[:i] + [new] + x[i + 1:]
        if len(x) >= 2:
            return [x[1], x[0]] + x[2:] if x[0] != x[1] else None
        return None
    if isinstance(x, dict):
        for k, v in x.items():
            new = _bump(v)
            if new is not None:
                return {**x, k: new}
        return None
    if isinstance(x, str) and x.lstrip("-").isdigit():
        return str(int(x) + 1)
    return None


def _steps(lesson: Lesson) -> list[int]:
    return [i for i, s in enumerate(lesson.scenes) if s.kind == "step"]


def wrong_state(lesson: Lesson) -> Iterator[Mutant]:
    for i in _steps(lesson):
        new = _bump(copy.deepcopy(lesson.scenes[i].claimed_state))
        if new is not None and new != lesson.scenes[i].claimed_state:
            m = lesson.model_copy(deep=True)
            m.scenes[i].claimed_state = new
            yield Mutant("wrong claimed_state", f"scene {i}", m)


def wrong_fact(lesson: Lesson) -> Iterator[Mutant]:
    """A fact the narration states ("the top is 7") changed to another value of the structure."""
    values = sorted({str(v) for v in re.findall(r"\b\d+\b", " ".join(s.narration for s in lesson.scenes))})
    for i, scene in enumerate(lesson.scenes):
        for fact, said in fact_claims(scene.narration, set(values)):
            for other in values:
                if other != said:
                    text = re.sub(rf"\b{re.escape(said)}\b", other, scene.narration, count=0)
                    if text != scene.narration:
                        m = lesson.model_copy(deep=True)
                        m.scenes[i].narration = text
                        yield Mutant("wrong fact in narration", f"scene {i}: {fact} {said} -> {other}", m)
                    break
            break


def invented_number(lesson: Lesson) -> Iterator[Mutant]:
    for i, scene in enumerate(lesson.scenes):
        match = re.search(r"(?<![\w.])\d+(?!\w)", scene.narration)
        if match and not re.match(r"(?:step|O\()", scene.narration[max(0, match.start() - 5):match.start()]):
            m = lesson.model_copy(deep=True)
            m.scenes[i].narration = scene.narration[:match.start()] + str(OUTSIDE) + scene.narration[match.end():]
            yield Mutant("invented number in narration", f"scene {i}", m)


def shifted_number(lesson: Lesson) -> Iterator[Mutant]:
    """Every number in a step's narration moved by one: the hard case, often still a plausible value."""
    for i in _steps(lesson):
        text = re.sub(r"(?<![\w.])(\d+)(?!\w)", lambda mt: str(int(mt.group(1)) + 1), lesson.scenes[i].narration)
        if text != lesson.scenes[i].narration:
            m = lesson.model_copy(deep=True)
            m.scenes[i].narration = text
            yield Mutant("every number in a step shifted by one", f"scene {i}", m)


def changed_argument(lesson: Lesson) -> Iterator[Mutant]:
    for i in _steps(lesson):
        op = lesson.scenes[i].op
        for key, value in (op.args if op else {}).items():
            new = _bump(value)
            if new is not None:
                m = lesson.model_copy(deep=True)
                m.scenes[i].op.args[key] = new
                yield Mutant("changed operation argument", f"scene {i}: {key}", m)


def dropped_step(lesson: Lesson) -> Iterator[Mutant]:
    """A step that changes the state left out. (Leaving out the last step, or a read-only one such as peek or
    search, leaves a correct, shorter lesson: nothing to catch.)"""
    from ..algorithms import build

    ds, changes = build(lesson.structure, lesson.initial), {}
    for i in _steps(lesson):
        before = repr(ds.state())
        ds.run(lesson.scenes[i].op.name, lesson.scenes[i].op.args)
        changes[i] = repr(ds.state()) != before
    for i in _steps(lesson)[:-1]:
        if changes[i]:
            m = lesson.model_copy(deep=True)
            del m.scenes[i]
            yield Mutant("dropped step", f"scene {i}", m)


def swapped_steps(lesson: Lesson) -> Iterator[Mutant]:
    steps = _steps(lesson)
    for a, b in zip(steps, steps[1:]):
        if lesson.scenes[a].op != lesson.scenes[b].op:
            m = lesson.model_copy(deep=True)
            m.scenes[a].op, m.scenes[b].op = m.scenes[b].op, m.scenes[a].op
            yield Mutant("two operations swapped", f"scenes {a} and {b}", m)


def wrong_quiz_answer(lesson: Lesson) -> Iterator[Mutant]:
    for k, q in enumerate(lesson.quiz):
        other = next((o for o in q.options if o != q.answer), None)
        if other is not None:
            m = lesson.model_copy(deep=True)
            m.quiz[k].answer = other
            yield Mutant("wrong quiz answer", f"question {k + 1}", m)


def changed_quiz_operations(lesson: Lesson) -> Iterator[Mutant]:
    for k, q in enumerate(lesson.quiz):
        if q.ops:
            m = lesson.model_copy(deep=True)
            m.quiz[k].ops = m.quiz[k].ops[:-1]
            yield Mutant("quiz operation dropped", f"question {k + 1}", m)


def changed_initial(lesson: Lesson) -> Iterator[Mutant]:
    new = _bump(copy.deepcopy(lesson.initial))
    if new is not None and new != lesson.initial:
        m = lesson.model_copy(deep=True)
        m.initial = new
        yield Mutant("changed initial data", "initial", m)


OPERATORS: list[Callable[[Lesson], Iterator[Mutant]]] = [
    wrong_state, wrong_fact, invented_number, shifted_number, changed_argument, dropped_step, swapped_steps,
    wrong_quiz_answer, changed_quiz_operations, changed_initial,
]


def trace(lesson: Lesson):
    """What a lesson teaches, as the simulator sees it: the state and facts after every step, every narration,
    and the true answer of every quiz question. Two lessons with the same trace teach the same thing."""
    from ..algorithms import OpError, build
    from .verifier import question_answer

    try:
        ds = build(lesson.structure, lesson.initial)
        steps = []
        for scene in lesson.scenes:
            if scene.kind == "step" and scene.op:
                ds.run(scene.op.name, scene.op.args)
                steps.append((repr(ds.state()), repr(ds.facts())))
        answers = []
        for q in lesson.quiz:
            try:
                answers.append(question_answer(lesson, q))
            except OpError:
                answers.append(None)
    except OpError:
        return None
    written = [(s.narration, repr(s.claimed_state), repr(s.claims)) for s in lesson.scenes]
    asked = [(q.answer, q.options, q.ask, q.claim) for q in lesson.quiz]
    return steps, written, answers, asked


def run(lesson: Lesson, keep_equivalent: bool = False) -> list[tuple[Mutant, bool]]:
    """Every mutant of one plan and whether the verifier caught it. Equivalent mutants (same trace as the
    original: dropping a read-only step, a quiz operation that does not change the answer) teach exactly the
    same thing (and say the same), so the verifier is right to accept them; they are left out unless asked for."""
    original = trace(lesson)
    out = []
    for operator in OPERATORS:
        for mutant in operator(lesson):
            if not keep_equivalent and trace(mutant.lesson) == original:
                continue
            try:
                caught = not verify_lesson(mutant.lesson).ok
            except Exception:  # a mutant that breaks the verifier itself is a bug, but it is not a silent pass
                caught = True
            out.append((mutant, caught))
    return out
