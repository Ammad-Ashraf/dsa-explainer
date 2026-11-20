"""Quiz generator. The language model writes multiple-choice questions about
the lesson; each question carries its own operations, so the verifier can run
them on the real data structure and confirm the answer. Wrong questions are
sent back once. A question whose answer is right but whose options are not
(the answer missing, two options alike) gets its options rebuilt from simulated
mistakes (mistakes.py) instead of being thrown away, and every wrong option
that a simulated mistake explains carries that reason. If too few questions
survive, questions are built from the lesson itself.
"""

from __future__ import annotations

import json
import zlib

from pydantic import ValidationError

from .. import events
from . import llm, schemas
from ..core.lesson import Lesson, Question
from .. import algorithms
from ..algorithms import OpError, build
from ..core.verifier import check_question, question_answer
from . import mistakes

QUIZ_TIMEOUT = 90  # seconds per request: the quiz is the least important part, so it never holds a lesson up for long

PROMPT = """Write {n} multiple-choice quiz questions for the end of a video lesson.
Lesson: "{title}" ({level} level) about a {structure}.
Lesson data: initial = {initial}; operations in order: {ops}; final state = {final}.

Structure reference:
{help}

A program checks every answer by running "ops" on a real {structure} that starts from "start" (null = the lesson's initial data). Work each answer out step by step.
Rules:
- Each question is at most 35 words and states its start data and its operations in words, so it can be solved without the video. Use different values or a different order than the lesson.
- "ask" is one fact name from: {facts}. Counts such as comparisons or swaps make good questions too.
- 3 or 4 options, all different, exactly one correct; "answer" is copied exactly from the correct option. Write list answers as values separated by commas, in the order of that fact. Good wrong options are what a typical mistake gives: forgetting the last operation, doing two in the wrong order, or treating one structure as another.
- At most one question may be true/false: give "claim" (a value of the asked fact), options ["True", "False"], and the answer True or False.
- "explanation" is one short spoken sentence giving the reason.
Return only JSON: {{"questions": [{{"question": "...", "start": <data or null>, "ops": [{{"name": "...", "args": {{}}}}], "ask": "...", "options": ["...", "..."], "answer": "...", "explanation": "...", "claim": null}}]}}"""


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
        reply = llm.chat(messages, schema=schemas.quiz(), timeout=QUIZ_TIMEOUT)
        try:
            questions = [Question.model_validate(q) for q in llm.parse_json(reply).get("questions", [])]
        except (ValidationError, ValueError) as exc:
            problems, good = [f"invalid reply: {str(exc)[:300]}"], []
        else:
            checked = [(q, check_question(lesson, q)) for q in (repair(lesson, q) for q in questions)]
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
    return (best + builtin_questions(lesson, n - len(best), avoid=best))[:n] if len(best) < n else best


def repair(lesson: Lesson, q: Question) -> Question:
    """Keep a question whose answer is right: rebuild broken options, and explain the wrong ones we can."""
    try:
        truth = question_answer(lesson, q)
    except OpError:
        return q  # check_question reports it
    if q.claim is not None or not mistakes._same(q.answer, truth):
        return q  # a true/false question, or a wrong answer: the model must fix it
    problem = check_question(lesson, q)
    try:
        if problem is None:
            reasons = mistakes.mistakes(lesson, q)
            q.why_wrong = {o: why for o in q.options for v, why in reasons.items() if mistakes._same(o, v)}
            return q
        if "option" in problem:
            return mistakes.with_options(lesson, q, keep=q.options)
    except OpError:
        pass
    return q


def _steps(lesson: Lesson) -> list:
    return [s.op for s in lesson.scenes if s.kind == "step" and s.op]


LIST_NAMES = {"items": "values, in order", "visited": "nodes visited so far, in order", "order": "order so far",
              "distances": "distances", "sorted": "sorted values", "table": "table", "merged": "merged values",
              "queue": "queue, front first", "stack": "stack, bottom first", "ready": "ready nodes", "chain": "chain"}
COUNT_QUESTIONS = {
    "comparisons": "How many comparisons did the last step of this video make?",
    "swaps": "How many swaps did the last step of this video make?",
    "shifts": "How many values did the last step of this video shift to the right?",
    "walked": "How many nodes did the last step of this video walk through?",
}


def _fact_label(cls, fact: str) -> str:
    if fact == "current" and cls.CATEGORY == "graphs":
        return "current node"
    return cls.FACT_LABELS.get(fact, fact.replace("_", " "))


def _short(title: str) -> str:
    return title.split(" (")[0].lower()


def _what(cls, fact: str) -> str:
    """'what is the top' or 'what are the values, in order'."""
    if fact in LIST_NAMES:
        return f"what are the {LIST_NAMES[fact]}"
    return f"what is the {_fact_label(cls, fact)}"


def _steps_text(k: int) -> str:
    return "the first step" if k == 1 else f"the first {k} steps"


def builtin_questions(lesson: Lesson, n: int = 2, avoid: list[Question] | None = None) -> list[Question]:
    """Questions built from the lesson itself: every answer computed, every wrong option a simulated mistake
    (or a near miss), each checked by the verifier like any other question."""
    cls = algorithms.get(lesson.structure)
    name, ops, title = algorithms.resolve(lesson.structure), _steps(lesson), _short(cls.TITLE)
    candidates: list[Question] = []
    main = mistakes.QUIZ_FACTS.get(cls.NAME) or next(iter(cls.STRIP), "size")
    candidates.append(Question(question=f"After all the steps of this {title}, {_what(cls, main)}?",
                               ops=ops, ask=main, options=["?", "?"], answer="?"))
    half = ops[: max(1, len(ops) // 2)]
    for fact in cls.STRIP:  # a true/false question about the middle of the lesson
        if fact == main or fact in LIST_NAMES:
            continue
        probe = Question(question="", ops=half, ask=fact, options=["True", "False"], answer="?")
        try:
            wrong = [w for w in mistakes.mistakes(lesson, probe) if w not in ("-", "empty")]
            truth = mistakes.answer(name, lesson.initial, half, fact)
        except OpError:
            continue
        if truth in ("-", "empty") or not wrong:
            continue
        claim = truth if zlib.crc32(lesson.title.encode()) % 2 else wrong[0]  # the answer is not always False
        candidates.append(Question(
            question=f"True or false: after {_steps_text(len(half))} of this video, the {_fact_label(cls, fact)} "
                     f"is {claim}.", ops=half, ask=fact, options=["True", "False"],
            answer="True" if claim == truth else "False", claim=claim,
            explanation=f"Running {_steps_text(len(half))} gives {truth}."))
        break
    for fact, text in COUNT_QUESTIONS.items():  # a count the simulator kept during the last step
        if fact in cls.FACTS and fact != main:
            candidates.append(Question(question=text, ops=ops, ask=fact, options=["?", "?"], answer="?"))
            break
    else:
        holder = {"graphs": "graph", "dp": "table"}.get(cls.CATEGORY, title)
        candidates.append(Question(question=f"After all the steps, how many {cls.NOUN} does the {holder} hold?",
                                   ops=ops, ask="size", options=["?", "?"], answer="?"))
    taken = {(q.ask, len(q.ops), q.claim) for q in avoid or []}
    out: list[Question] = []
    for q in candidates:
        if len(out) >= n or (q.ask, len(q.ops), q.claim) in taken:
            continue
        if q.claim is None:
            try:
                q = mistakes.with_options(lesson, q)
            except OpError:
                continue
            q.explanation = f"Running the operations on the real {title} gives {q.answer}."
        if check_question(lesson, q) is None:
            out.append(q)
    return out


def fallback_question(lesson: Lesson) -> Question:
    """One question built from the lesson itself (kept for older callers)."""
    return builtin_questions(lesson, 1)[0]
