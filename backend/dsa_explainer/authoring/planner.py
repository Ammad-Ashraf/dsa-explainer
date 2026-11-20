"""Lesson planner: topic + learner level -> a verified scene plan (JSON).

The language model never draws and never has the last word on facts. It
writes a plan; the verifier runs the plan on the real data structure; any
error goes back to the model with the true state so it can fix the plan.
After MAX_ATTEMPTS failed attempts no video is made: a wrong video is worse
than no video.
"""

from __future__ import annotations

from pydantic import ValidationError

from .. import config, events
from . import llm, schemas
from ..core.lesson import Lesson
from .. import algorithms
from ..core.verifier import MAX_STEPS, MIN_WORDS, verify_lesson


class PlanError(RuntimeError):
    """The topic is unsupported, or no correct plan could be made."""


SYSTEM_PROMPT = """You are the lesson planner of DSA Explainer, which turns a data-structures topic into a narrated, animated video.
You do not draw anything. You write a JSON scene plan. A renderer draws it, and a verifier runs every step on a real data structure: a plan with a wrong claimed_state or a narration that contradicts the true state is rejected.

Supported algorithms and structures (use exactly these names, operations and state formats):
{catalog}

Return ONLY one JSON object of this shape:
{{
  "topic": "<the learner's request>",
  "level": "beginner | intermediate | advanced",
  "title": "<video title, at most 40 characters>",
  "structure": "<{names}>",
  "initial": <initial data in that structure's format>,
  "scenes": [
    {{"kind": "intro", "caption": "<at most 50 characters>", "narration": "<...>"}},
    {{"kind": "step", "caption": "<at most 50 characters, e.g. push(7)>",
      "op": {{"name": "push", "args": {{"value": 7}}}},
      "claimed_state": <the full state AFTER this step, in the state format>,
      "narration": "<...>"}},
    {{"kind": "summary", "caption": "Summary", "points": ["<at most 60 characters>", "..."], "narration": "<...>"}}
  ]
}}

Rules:
- One intro scene first, one summary scene last, and 4 to {max_steps} step scenes between them, one operation each.
- Work out claimed_state carefully, one step at a time, starting from "initial".
- The narration is spoken aloud: plain sentences, no markdown, no symbols such as -> or brackets. Write numbers as digits. Each scene has 2 to 4 sentences (25 to 60 words); the whole narration has at least {min_words} words. Explain what happens in the step and why.
- In a step's narration only mention values that are in the structure or in that step's operation. Whenever you name the top, front, rear, head, tail, root, size or current node, it must be true right after that step.
- Use small values (whole numbers from 1 to 99, or single capital letters for graph nodes) and at most 7 items or nodes, so the picture stays readable.
- Level: beginner = everyday analogies and simple words; intermediate = precise terms and time complexity; advanced = complexity, edge cases and trade-offs.
- If the learner gives their own data (values, a list of edges, a start node), use it as "initial".
- Summary: 3 or 4 short points.
- If the topic is not about one of the supported algorithms or structures, return {{"error": "unsupported", "message": "<one sentence saying what is supported>"}}.
{also}"""


def system_prompt(topic: str = "") -> str:
    """The planner's instructions. When the topic names an algorithm, only its reference is included
    (a shorter prompt, and fewer chances to mix formats); the full list is still named."""
    picked = algorithms.candidates(topic)
    names = [cls.NAME for cls in (picked or algorithms.ALL)]
    also = ("" if not picked else "Also supported (ask for these by name): "
            + ", ".join(cls.NAME for cls in algorithms.ALL if cls not in picked) + ".")
    return SYSTEM_PROMPT.format(catalog=algorithms.catalog(names), names=" | ".join(names),
                                max_steps=MAX_STEPS - 2, min_words=MIN_WORDS + 20, also=also)


def _check(reply: str) -> tuple[Lesson | None, list[str]]:
    """Parse and verify one reply: the lesson (if it parsed) and every problem found."""
    try:
        data = llm.parse_json(reply)
        if data.get("error"):
            raise PlanError(data.get("message") or "This topic is not supported.")
        lesson = Lesson.model_validate(data)
    except ValidationError as exc:
        return None, [f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()[:6]]
    except ValueError as exc:  # not JSON
        return None, [f"the reply is not valid JSON ({exc})"]
    return lesson, verify_lesson(lesson).errors


def plan_lesson(topic: str, level: str = "beginner", log=print) -> tuple[Lesson, list[str]]:
    """A verified lesson plan, and the problems the verifier found on the way."""
    messages = [
        {"role": "system", "content": system_prompt(topic)},
        {"role": "user", "content": f"Topic: {topic.strip()}\nLearner level: {level}"},
    ]
    history: list[str] = []
    for attempt in range(1, config.MAX_ATTEMPTS + 1):
        log(f"Planning the lesson (attempt {attempt})", 0.05 + 0.05 * attempt)
        reply = llm.chat(messages, schema=schemas.lesson_plan())
        lesson, problems = _check(reply)
        if not problems:
            lesson.level = level if level in ("beginner", "intermediate", "advanced") else lesson.level
            return lesson, history
        history.append(f"attempt {attempt}: " + problems[0])
        events.emit(log, "rejected", stage="plan", attempt=attempt, reason=problems[0])
        messages += [
            {"role": "assistant", "content": reply},
            {"role": "user", "content": "The verifier rejected your plan:\n- " + "\n- ".join(problems[:8])
             + "\nFix every problem and return the complete corrected JSON object only."},
        ]
    raise PlanError(f"No correct plan after {config.MAX_ATTEMPTS} attempts, so no video was made. "
                    f"Last problem: {history[-1]}")
