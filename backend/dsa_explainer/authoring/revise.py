"""Revision control. The learner asks for a change ("slow down step 4",
"explain it for a beginner") and only the scenes it is about change.

Speed requests are handled by rules. Anything else goes to the language model,
which may only rewrite narration, captions, summary points and speed: the
operations and values are fixed, so the pictures stay verified. The revised
lesson is verified again, and because video clips are cached by their content,
only the changed scenes are rendered again.
"""

from __future__ import annotations

import json
import re

from pydantic import ValidationError

from .. import events
from ..core.lesson import Lesson, scene_labels
from ..core.verifier import verify_lesson
from . import llm


class RevisionError(RuntimeError):
    pass


_SLOWER = re.compile(r"\b(slow|slower)\b", re.IGNORECASE)
_FASTER = re.compile(r"\b(speed\s+up|faster|quicker)\b", re.IGNORECASE)
_OTHER = re.compile(r"\b(explain|simpl|detail|example|beginner|advanced|rewrite|again|word|say|why|how)", re.IGNORECASE)
_SCENE = re.compile(r"\b(step\s+\d+|intro|summary)\b", re.IGNORECASE)

PROMPT = """You revise an existing data-structures video. The learner asked: "{request}"
The scenes are listed below with their caption, the TRUE state after each scene (the pictures cannot change) and the current narration.
{scenes}

Change only the scenes the request is about; if it is about the whole video (for example "explain it for a beginner"), change every scene.
You may change: "narration" (spoken, plain sentences, numbers as digits, 2 to 5 sentences), "caption" (at most 50 characters), "speed" (0.5 to 1.5, lower is slower) and "points" (summary only).
Every fact must stay true: only mention values from that scene's state or operation, and any top, front, rear, head, tail, root, size or current node you name must match the true state.
Return only JSON: {{"level": "<beginner | intermediate | advanced, only if the request changes it>", "changes": [{{"scene": "<label as listed, e.g. step 2>", "narration": "...", "caption": "...", "speed": 1.0, "points": ["..."]}}]}}"""


def is_rule_based(request: str) -> bool:
    """True for pure speed changes, which need no language model."""
    return bool((_SLOWER.search(request) or _FASTER.search(request)) and not _OTHER.search(request))


def revise(lesson: Lesson, request: str, log=print, attempts: int = 3) -> tuple[Lesson, list[str]]:
    """The revised lesson and the labels of the scenes that changed."""
    request = request.strip()
    if not request:
        raise RevisionError("Type what you want changed, for example 'slow down step 2'.")
    if is_rule_based(request):
        new = _change_speed(lesson, request)
    else:
        new = _rewrite(lesson, request, log, attempts)
    changed = [label for label, a, b in zip(scene_labels(lesson), lesson.scenes, new.scenes) if a != b]
    if not changed and new.level == lesson.level:
        raise RevisionError("Nothing changed. Try naming a part, for example 'explain step 2 more simply'.")
    return new, changed


def _targets(lesson: Lesson, request: str) -> list[int]:
    labels = scene_labels(lesson)
    named = [re.sub(r"\s+", " ", m.lower()) for m in _SCENE.findall(request)]
    for name in named:
        if name not in labels:
            steps = sum(label.startswith("step") for label in labels)
            raise RevisionError(f"There is no {name}: this video has an intro, steps 1 to {steps} and a summary.")
    return [labels.index(n) for n in named] or list(range(len(labels)))


def _change_speed(lesson: Lesson, request: str) -> Lesson:
    new = lesson.model_copy(deep=True)
    factor = 0.75 if _SLOWER.search(request) else 1.25
    for i in _targets(lesson, request):
        new.scenes[i].speed = min(1.5, max(0.5, round(new.scenes[i].speed * factor, 2)))
    return new


def _scene_table(lesson: Lesson) -> str:
    report = verify_lesson(lesson)
    lines = []
    for label, scene, frame in zip(scene_labels(lesson), lesson.scenes, report.frames):
        op = f" | operation: {scene.op.describe()}" if scene.op else ""
        lines.append(f"{label}: caption: {scene.caption!r}{op} | true state: {json.dumps(frame.state)} | "
                     f"speed: {scene.speed} | narration: {scene.narration}")
    return "\n".join(lines)


def _apply(lesson: Lesson, data: dict) -> Lesson:
    new = lesson.model_copy(deep=True)
    index = {label: i for i, label in enumerate(scene_labels(lesson))}
    for change in data.get("changes") or []:
        label = re.sub(r"\s+", " ", str(change.get("scene", "")).strip().lower())
        if label not in index:
            raise ValueError(f"unknown scene {change.get('scene')!r}; use one of: {', '.join(index)}")
        scene = new.scenes[index[label]]
        for key in ("narration", "caption", "speed", "points"):
            if change.get(key) not in (None, "", []):
                setattr(scene, key, change[key])
    if data.get("level") in ("beginner", "intermediate", "advanced"):
        new.level = data["level"]
    return Lesson.model_validate(new.model_dump())  # re-check field limits (speed, lengths)


def _rewrite(lesson: Lesson, request: str, log, attempts: int) -> Lesson:
    messages = [{"role": "user", "content": PROMPT.format(request=request, scenes=_scene_table(lesson))}]
    problems: list[str] = []
    for attempt in range(1, attempts + 1):
        log(f"Rewriting the requested part (attempt {attempt})", 0.15)
        reply = llm.chat(messages)
        try:
            new = _apply(lesson, llm.parse_json(reply))
        except (ValidationError, ValueError) as exc:
            problems = [str(exc)[:300]]
        else:
            problems = verify_lesson(new).errors
            if not problems:
                return new
        events.emit(log, "rejected", stage="revise", attempt=attempt, reason=problems[0])
        messages += [{"role": "assistant", "content": reply},
                     {"role": "user", "content": "The verifier rejected this revision:\n- " + "\n- ".join(problems[:8])
                      + "\nFix it and return the same JSON object."}]
    raise RevisionError(f"The revision could not be verified, so the video was kept as it was. {problems[0]}")
