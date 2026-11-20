import json

from dsa_explainer.config import PLANS_DIR as EXAMPLES_DIR
from dsa_explainer.core.lesson import Lesson

EXAMPLES = sorted(p.stem for p in EXAMPLES_DIR.glob("*.json"))


def load(name: str) -> Lesson:
    return Lesson.model_validate_json((EXAMPLES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def raw(name: str) -> dict:
    return json.loads((EXAMPLES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def fake_llm(monkeypatch, replies: list[str]) -> list[list[dict]]:
    """Replace the API with canned replies; returns the messages each call received."""
    from dsa_explainer.authoring import llm

    calls, queue = [], list(replies)

    def chat(messages, temperature=None, schema=None, timeout=None):
        calls.append([dict(m) for m in messages])
        return queue.pop(0)

    monkeypatch.setattr(llm, "chat", chat)
    return calls
