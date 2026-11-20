import json

import pytest

from dsa_explainer import config
from dsa_explainer.authoring import llm, planner

from .helpers import fake_llm, raw


def quiet(*_):
    pass


def test_wrong_plan_is_sent_back_with_the_true_state(monkeypatch):
    good = raw("stack")
    good.pop("quiz")
    bad = json.loads(json.dumps(good))
    bad["scenes"][1]["claimed_state"] = [4, 9]  # the model forgot the pushed value
    calls = fake_llm(monkeypatch, [json.dumps(bad), "```json\n" + json.dumps(good) + "\n```"])

    lesson, rejected = planner.plan_lesson("How does a stack work?", "beginner", log=quiet)

    assert lesson.title == good["title"]
    assert len(rejected) == 1 and "claimed_state" in rejected[0]
    assert "[4, 9, 2]" in calls[1][-1]["content"]  # the repair request names the real state


def test_unsupported_topic_is_refused(monkeypatch):
    fake_llm(monkeypatch, ['{"error": "unsupported", "message": "Only stacks, queues, lists, BSTs and BFS."}'])
    with pytest.raises(planner.PlanError, match="Only stacks"):
        planner.plan_lesson("Explain transformers", "beginner", log=quiet)


def test_no_video_after_too_many_wrong_plans(monkeypatch):
    fake_llm(monkeypatch, ["not json at all"] * config.MAX_ATTEMPTS)
    with pytest.raises(planner.PlanError, match="No correct plan"):
        planner.plan_lesson("stack", "beginner", log=quiet)


def fake_client(create, model="main", fallback=""):
    """An llm.Client whose API calls go to `create(**kwargs)`."""
    client = llm.Client(llm.LLMSettings("test", "https://example.invalid/v1", "sk-test", model, fallback))
    completions = type("Completions", (), {"create": staticmethod(create)})
    client._openai = type("OpenAI", (), {"chat": type("Chat", (), {"completions": completions})})
    return client


def rate_limit(message="rate limited"):
    import httpx
    from openai import RateLimitError

    request = httpx.Request("POST", "https://example.invalid/chat/completions")
    return RateLimitError(message, response=httpx.Response(429, request=request), body=None)


def test_rate_limit_waits_then_retries(monkeypatch):
    replies, waits = [rate_limit(), rate_limit(), "ok"], []

    def create(**kwargs):
        reply = replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply

    monkeypatch.setattr(llm.time, "sleep", waits.append)
    assert fake_client(create)._create(messages=[]) == "ok"
    assert waits == [10, 20]


def test_daily_limit_switches_to_fallback_model(monkeypatch):
    daily, seen = rate_limit("Quota exceeded: GenerateRequestsPerDayPerProjectPerModel-FreeTier"), []

    def create(**kwargs):
        seen.append(kwargs["model"])
        if kwargs["model"] == "main":
            raise daily
        return "ok"

    monkeypatch.setattr(llm.time, "sleep", lambda s: pytest.fail("a daily limit should not wait"))
    client = fake_client(create, fallback="lite")
    assert client._create(messages=[]) == "ok"
    assert seen == ["main", "lite"] and client.model_in_use() == "lite"


def test_parse_json_tolerates_fences_and_text():
    assert llm.parse_json('Here you go:\n```json\n{"a": 1}\n```') == {"a": 1}
    with pytest.raises(ValueError):
        llm.parse_json("no json here")
