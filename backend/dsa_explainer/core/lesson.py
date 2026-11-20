"""The scene plan: the JSON the language model writes, as Pydantic models.
A plan that does not fit these models is rejected before anything else runs."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Level = Literal["beginner", "intermediate", "advanced"]


class Op(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)

    def describe(self) -> str:
        return f"{self.name}({', '.join(str(v) for v in self.args.values())})"


class Scene(BaseModel):
    kind: Literal["intro", "step", "summary"]
    narration: str = Field(min_length=10)
    caption: str = ""
    op: Op | None = None  # step scenes only
    claimed_state: Any = None  # the planner's belief about the state after the op
    points: list[str] = Field(default_factory=list)  # summary bullet points
    speed: float = Field(default=1.0, ge=0.5, le=1.5)  # < 1 is slower (revisions)


class Question(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    question: str
    start: Any = None  # data in the structure's initial format; None = the lesson's initial data
    ops: list[Op] = Field(default_factory=list)
    ask: str  # a fact name, e.g. "top"
    options: list[str] = Field(min_length=2, max_length=4)
    answer: str
    explanation: str = ""


class Lesson(BaseModel):
    topic: str
    level: Level
    title: str
    structure: str
    initial: Any
    scenes: list[Scene]
    quiz: list[Question] = Field(default_factory=list)
    provenance: dict[str, Any] | None = None  # who wrote a saved plan, and how it was checked


def scene_labels(lesson: Lesson) -> list[str]:
    """Names learners use for scenes: intro, step 1, step 2, ..., summary."""
    labels, step = [], 0
    for scene in lesson.scenes:
        if scene.kind == "step":
            step += 1
            labels.append(f"step {step}")
        else:
            labels.append(scene.kind)
    return labels
