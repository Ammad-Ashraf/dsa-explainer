import json
from pathlib import Path

from dsa_explainer.lesson import Lesson

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
EXAMPLES = sorted(p.stem for p in EXAMPLES_DIR.glob("*.json"))


def load(name: str) -> Lesson:
    return Lesson.model_validate_json((EXAMPLES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def raw(name: str) -> dict:
    return json.loads((EXAMPLES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def fake_llm(monkeypatch, replies: list[str]) -> list[list[dict]]:
    """Replace the API with canned replies; returns the messages each call received."""
    from dsa_explainer import llm

    calls, queue = [], list(replies)

    def chat(messages, temperature=None):
        calls.append([dict(m) for m in messages])
        return queue.pop(0)

    monkeypatch.setattr(llm, "chat", chat)
    return calls
