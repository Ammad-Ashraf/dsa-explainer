"""Quiz generator. The language model writes multiple-choice questions about
the lesson; each question carries its own operations, so the verifier can run
them on the real data structure and confirm the answer. Wrong questions are
sent back once; if none survive, a question is built from the lesson itself.
"""

from __future__ import annotations

import json

from pydantic import ValidationError

from .. import events
from . import llm, schemas
from ..core.lesson import Lesson, Question
from .. import algorithms
from ..algorithms import build, fact_text
from ..core.verifier import check_question

PROMPT = """Write {n} multiple-choice quiz questions for the end of a video lesson.
Lesson: "{title}" ({level} level) about a {structure}.
Lesson data: initial = {initial}; operations in order: {ops}; final state = {final}.

Structure reference:
{help}

A program checks every answer by running "ops" on a real {structure} that starts from "start" (null = the lesson's initial data). Work each answer out step by step.
Rules:
- Each question is at most 35 words and states its start data and its operations in words, so it can be solved without the video. Use different values or a different order than the lesson.
- "ask" is one fact name from: {facts}.
- 3 or 4 options, all different, exactly one correct; "answer" is copied exactly from the correct option. Write list answers as values separated by commas, in the order of that fact.
- "explanation" is one short spoken sentence giving the reason.
Return only JSON: {{"questions": [{{"question": "...", "start": <data or null>, "ops": [{{"name": "...", "args": {{}}}}], "ask": "...", "options": ["...", "..."], "answer": "...", "explanation": "..."}}]}}"""


def _prompt(lesson: Lesson, n: int) -> str:
    cls = algorithms.get(lesson.structure)
    ds = build(lesson.structure, lesson.initial)
    ops = [s.op for s in lesson.scenes if s.kind == "step" and s.op]
    for op in ops:
        ds.run(op.name, op.args)
    return PROMPT.format(
        n=n, title=lesson.title, level=lesson.level, structure=lesson.structure, help=cls.HELP,
        initial=json.dumps(lesson.initial), ops=", ".join(op.describe() for op in ops),
        final=json.dumps(ds.state()), facts=", ".join(cls.FACTS),
    )


def make_quiz(lesson: Lesson, n: int = 2, attempts: int = 2, log=print) -> list[Question]:
    messages = [{"role": "user", "content": _prompt(lesson, n)}]
    best: list[Question] = []
    for attempt in range(1, attempts + 1):
        log(f"Writing the quiz (attempt {attempt})", 0.3)
        reply = llm.chat(messages, schema=schemas.quiz())
        try:
            questions = [Question.model_validate(q) for q in llm.parse_json(reply).get("questions", [])]
        except (ValidationError, ValueError) as exc:
            problems, good = [f"invalid reply: {str(exc)[:300]}"], []
        else:
            checked = [(q, check_question(lesson, q)) for q in questions]
            good = [q for q, problem in checked if problem is None]
            problems = [f"question {i}: {p}" for i, (_, p) in enumerate(checked, 1) if p]
        if len(good) > len(best):
            best = good
        if len(best) >= n:
            return best[:n]
        events.emit(log, "rejected", stage="quiz", attempt=attempt, reason=problems[0] if problems else "too few questions")
        messages += [{"role": "assistant", "content": reply},
                     {"role": "user", "content": "Problems:\n- " + "\n- ".join(problems or ["too few questions"])
                      + f"\nReturn {n} corrected questions as the same JSON object."}]
    return best or [fallback_question(lesson)]


def fallback_question(lesson: Lesson) -> Question:
    """A question built from the lesson itself, with a computed answer."""
    ops = [s.op for s in lesson.scenes if s.kind == "step" and s.op]
    q = Question(question="", ops=ops, ask="size", options=["0", "1"], answer="0")
    ds = build(lesson.structure, lesson.initial)
    for op in ops:
        ds.run(op.name, op.args)
    size = int(fact_text(ds.facts()["size"]))
    cls = algorithms.get(lesson.structure)
    q.question = f"After all the steps in this video, how many {cls.NOUN} does the {cls.TITLE.lower()} have?"
    q.options = [str(v) for v in sorted({max(0, size - 1), size, size + 1, size + 2})]
    q.answer = str(size)
    q.explanation = f"Counting them in the final picture gives {size}."
    return q
