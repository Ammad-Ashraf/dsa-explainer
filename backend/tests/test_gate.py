"""The topic gate: off-topic requests are turned away before the planning call."""

import pytest
from dsa_explainer import config, pipeline
from dsa_explainer.authoring import gate, llm, planner

from .helpers import fake_llm
from .test_pipeline import Recorder


def test_a_named_algorithm_passes_without_an_api_call(monkeypatch):
    calls = fake_llm(monkeypatch, [])
    verdict = gate.check_topic("Explain bubble sort on 5 3 8 1")
    assert verdict.in_scope and verdict.source == "keyword" and verdict.structure == "bubble_sort"
    assert calls == []


def test_an_off_topic_request_is_turned_away_by_the_classifier(monkeypatch):
    calls = fake_llm(monkeypatch, ['{"in_scope": false, "structure": null, "reason": "geography question"}'])
    verdict = gate.check_topic("What is the capital of Pakistan")
    assert not verdict.in_scope and verdict.source == "model" and verdict.structure is None
    assert len(calls) == 1 and "dijkstra" in calls[0][0]["content"]  # the prompt lists the supported names


def test_a_paraphrase_is_accepted_and_names_its_algorithm(monkeypatch):
    fake_llm(monkeypatch, ['{"in_scope": true, "structure": "dijkstra", "reason": "shortest route"}'])
    verdict = gate.check_topic("How does a map app find the quickest route between two cities?")
    assert verdict.in_scope and verdict.structure == "dijkstra"


def test_an_unknown_structure_name_is_dropped(monkeypatch):
    fake_llm(monkeypatch, ['{"in_scope": true, "structure": "red_black_tree", "reason": "a tree"}'])
    verdict = gate.check_topic("rotations that keep a tree balanced")
    assert verdict.in_scope and verdict.structure is None


@pytest.mark.parametrize("reply", ["not json", '{"in_scope": "maybe"}', "{}", llm.LLMError("Request timed out.")])
def test_the_gate_fails_open(monkeypatch, reply):
    """A broken or slow classifier never blocks a topic: the planner decides, as before."""
    def chat(*args, **kwargs):
        if isinstance(reply, Exception):
            raise reply
        return reply

    monkeypatch.setattr(llm, "chat", chat)
    verdict = gate.check_topic("something the keywords do not know")
    assert verdict.in_scope and verdict.source == "fallback"


def test_the_gate_can_be_turned_off(monkeypatch):
    calls = fake_llm(monkeypatch, [])
    monkeypatch.setattr(config, "TOPIC_GATE", False)
    assert gate.check_topic("What is the capital of Pakistan").in_scope
    assert calls == []


def test_the_pipeline_stops_in_the_plan_stage_without_planning(monkeypatch):
    fake_llm(monkeypatch, ['{"in_scope": false, "structure": null, "reason": "geography question"}'])
    monkeypatch.setattr(planner, "plan_lesson", lambda *a, **k: pytest.fail("the planner should not run"))
    rep = Recorder()
    with pytest.raises(planner.PlanError, match="only explains data structures and algorithms"):
        pipeline.make_lesson("What is the capital of Pakistan", "beginner", "draft", rep)
    plan = [d for t, d in rep.events if t == "stage" and d["stage"] == "plan"]
    assert [d["status"] for d in plan] == ["running", "failed"]
    assert [d for t, d in rep.events if t == "gate"][0]["in_scope"] is False


def test_the_gate_s_pick_narrows_the_planner_prompt(monkeypatch):
    fake_llm(monkeypatch, ['{"in_scope": true, "structure": "dijkstra", "reason": "shortest route"}'])
    seen = {}

    def plan(topic, level, log, structure=None):
        seen["structure"] = structure
        raise planner.PlanError("stop here")

    monkeypatch.setattr(planner, "plan_lesson", plan)
    with pytest.raises(planner.PlanError):
        pipeline.make_lesson("quickest route between two cities", "beginner", "draft", Recorder())
    assert seen["structure"] == "dijkstra"
    prompt = planner.system_prompt("quickest route between two cities", "dijkstra")
    assert "Also supported" in prompt and "structure\": \"<dijkstra>" in prompt


def _quick_client(create):
    """An llm.Client whose API calls go to `create(**kwargs)`."""
    client = llm.Client(llm.LLMSettings("test", "https://example.invalid/v1", "sk-test", "main", "lite"))
    completions = type("Completions", (), {"create": staticmethod(create)})
    api = type("OpenAI", (), {"chat": type("Chat", (), {"completions": completions})})
    client._openai = api
    return client


def _reply(text):
    message = type("Message", (), {"content": text})
    return type("Reply", (), {"choices": [type("Choice", (), {"message": message})]})


def test_a_quick_call_uses_the_given_model_at_low_reasoning_effort():
    seen = []
    client = _quick_client(lambda **kwargs: seen.append(kwargs) or _reply('{"in_scope": true}'))
    client.chat([{"role": "user", "content": "hi"}], model="lite", quick=True)
    assert seen[0]["model"] == "lite" and seen[0]["reasoning_effort"] == "low"
    client.chat([{"role": "user", "content": "hi"}])  # ordinary calls are unchanged
    assert seen[1]["model"] == "main" and "reasoning_effort" not in seen[1]


def test_a_provider_without_reasoning_effort_is_asked_again_without_it():
    import httpx
    from openai import BadRequestError

    seen = []

    def create(**kwargs):
        seen.append(kwargs)
        if "reasoning_effort" in kwargs:
            response = httpx.Response(400, request=httpx.Request("POST", "https://example.invalid"))
            raise BadRequestError("Unrecognized request argument supplied: reasoning_effort", response=response,
                                  body=None)
        return _reply("{}")

    client = _quick_client(create)
    client.chat([{"role": "user", "content": "hi"}], quick=True)
    client.chat([{"role": "user", "content": "hi"}], quick=True)
    assert ["reasoning_effort" in k for k in seen] == [True, False, False]  # remembered after the first refusal


def test_a_quick_call_does_not_wait_on_a_rate_limit(monkeypatch):
    from .test_planner import rate_limit

    def create(**kwargs):
        raise rate_limit()

    monkeypatch.setattr(llm.time, "sleep", lambda s: pytest.fail("a quick call should not wait"))
    with pytest.raises(llm.LLMError, match="rate limit"):
        _quick_client(create).chat([{"role": "user", "content": "hi"}], quick=True)
