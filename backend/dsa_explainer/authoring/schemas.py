"""JSON Schemas for structured output, made from the Pydantic models.

Providers that support schema-constrained output (llm.Client's "json_schema"
mode) get these, so fewer replies are malformed and fewer repair rounds are
needed. They only shape the reply: Pydantic and the verifier still check it.
"""

from __future__ import annotations

from functools import cache

from ..core.lesson import Lesson, Question


@cache
def lesson_plan() -> dict:
    schema = Lesson.model_json_schema()
    schema["title"] = "lesson_plan"
    # the planner may refuse an unsupported topic with {"error": ..., "message": ...}
    schema["properties"]["error"] = {"type": "string"}
    schema["properties"]["message"] = {"type": "string"}
    schema.pop("required", None)  # required fields are enforced by Pydantic afterwards
    return schema


@cache
def quiz() -> dict:
    question = Question.model_json_schema()
    defs = question.pop("$defs", {})
    defs["Question"] = question
    return {"title": "quiz", "type": "object", "$defs": defs,
            "properties": {"questions": {"type": "array", "items": {"$ref": "#/$defs/Question"}}},
            "required": ["questions"]}
