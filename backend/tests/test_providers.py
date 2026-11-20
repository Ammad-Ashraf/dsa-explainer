"""Bring-your-own-key: presets, saved choices, JSON modes, and keys that never leak."""

import json

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import BadRequestError

from dsa_explainer import config
from dsa_explainer.api import create_app
from dsa_explainer.authoring import llm, providers, schemas

KEY = "sk-secret-0123456789abcdef"


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SETTINGS_FILE", tmp_path / "settings.json")
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path / "outputs")
    monkeypatch.setattr(config, "LLM_API_KEY", "")
    return tmp_path


def fake_client(create, settings=None):
    client = llm.Client(settings or llm.LLMSettings("test", "https://example.invalid/v1", KEY, "main"))
    completions = type("Completions", (), {"create": staticmethod(create)})
    client._openai = type("OpenAI", (), {"chat": type("Chat", (), {"completions": completions})})
    return client


def reply(text):
    message = type("Message", (), {"content": text})
    return type("Reply", (), {"choices": [type("Choice", (), {"message": message})]})


def bad_request(text):
    request = httpx.Request("POST", "https://example.invalid/v1/chat/completions")
    return BadRequestError(text, response=httpx.Response(400, request=request), body=None)


def test_nothing_configured_means_no_client(home):
    assert providers.resolve() is None and not llm.configured()
    with pytest.raises(llm.LLMError):
        llm.chat([{"role": "user", "content": "hi"}])


def test_env_key_is_the_default(home, monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", KEY)
    s = llm.active_settings()
    assert s.provider == "env" and s.api_key == KEY and s.model == config.LLM_MODEL


def test_saved_provider_wins_and_keys_are_never_described(home):
    providers.save("groq", {"api_key": KEY}, activate=True)
    s = llm.active_settings()
    assert s.provider == "groq" and s.model == providers.PRESETS["groq"].default_model
    described = json.dumps(providers.describe(), ensure_ascii=False)
    assert KEY not in described and "…cdef" in described
    groq = next(p for p in providers.describe()["providers"] if p["id"] == "groq")
    assert groq["saved"]["key_set"] and groq["ready"]


def test_presets_without_a_default_model_need_one(home):
    providers.save("openai", {"api_key": KEY}, activate=True)
    assert llm.active_settings() is None
    providers.save("openai", {"model": "some-model"})
    assert llm.active_settings().model == "some-model"


def test_local_providers_need_no_key(home):
    providers.activate("ollama")
    s = llm.active_settings()
    assert s.provider == "ollama" and s.base_url.startswith("http://127.0.0.1")


def test_bad_input_is_refused(home):
    with pytest.raises(providers.ProviderError):
        providers.save("nope", {"api_key": KEY})
    with pytest.raises(providers.ProviderError):
        providers.save("custom", {"base_url": "file:///etc/passwd"})
    with pytest.raises(providers.ProviderError):
        providers.save("gemini", {"password": "x"})


def test_an_empty_value_clears_a_saved_key(home):
    providers.save("gemini", {"api_key": KEY}, activate=True)
    providers.save("gemini", {"api_key": ""})
    assert llm.active_settings() is None


def test_json_mode_steps_down_when_the_provider_lacks_it():
    seen = []

    def create(**kwargs):
        mode = kwargs.get("response_format", {}).get("type", "none")
        seen.append(mode)
        if mode != "none":
            raise bad_request(f"response_format type {mode} is not supported")
        return reply('{"ok": true}')

    client = fake_client(create, llm.LLMSettings("t", "https://x.invalid", KEY, "m", structured="json_schema"))
    assert client.chat([], schema=schemas.quiz()) == '{"ok": true}'
    assert seen == ["json_schema", "json_object", "none"] and client.mode == "none"
    client.chat([])  # remembered: no more failed attempts
    assert seen[-1] == "none" and len(seen) == 4


def test_json_schema_mode_sends_the_schema():
    sent = {}

    def create(**kwargs):
        sent.update(kwargs)
        return reply("{}")

    client = fake_client(create, llm.LLMSettings("t", "https://x.invalid", KEY, "m", structured="json_schema"))
    client.chat([], schema=schemas.lesson_plan())
    spec = sent["response_format"]["json_schema"]
    assert spec["name"] == "lesson_plan" and "scenes" in spec["schema"]["properties"]
    assert "error" in spec["schema"]["properties"]  # the planner can still refuse a topic


def test_unexpected_errors_are_scrubbed_of_keys(home, monkeypatch):
    def create(**kwargs):
        raise RuntimeError(f"connection failed for key {KEY}")

    client = fake_client(create)
    monkeypatch.setattr(llm, "current", lambda: client)
    monkeypatch.setattr(config, "LLM_API_KEY", KEY)
    with pytest.raises(llm.LLMError) as caught:
        llm.chat([{"role": "user", "content": "hi"}])
    assert KEY not in str(caught.value) and "[key]" in str(caught.value)


def test_each_configuration_keeps_its_own_fallback_state():
    a = llm.client_for(llm.LLMSettings("a", "https://a.invalid", "k1", "m", "lite"))
    b = llm.client_for(llm.LLMSettings("b", "https://b.invalid", "k2", "m", "lite"))
    a.on_fallback = True
    assert b.model_in_use() == "m" and a.model_in_use() == "lite"
    with llm.use(b.settings):
        assert llm.current() is b


def test_provider_api_never_returns_a_key(home):
    with TestClient(create_app()) as client:
        assert client.get("/api/health").json()["llm"]["configured"] is False
        saved = client.put("/api/providers/gemini", json={"api_key": KEY, "activate": True})
        assert saved.status_code == 200 and KEY not in saved.text
        assert client.get("/api/providers").json()["in_use"]["provider"] == "gemini"
        assert KEY not in client.get("/api/providers").text
        health = client.get("/api/health").json()["llm"]
        assert health["configured"] and health["model"] == "gemini-3.5-flash" and KEY not in json.dumps(health)
        assert client.post("/api/providers/active", json={"provider": "nope"}).status_code == 400


def test_provider_test_endpoint_reports_failures_without_the_key(home, monkeypatch):
    def check(self):
        raise RuntimeError(f"401 for {self.settings.api_key}")

    monkeypatch.setattr(llm.Client, "check", check)
    with TestClient(create_app()) as client:
        result = client.post("/api/providers/groq/test", json={"api_key": KEY}).json()
        assert result["ok"] is False and KEY not in json.dumps(result)
        assert client.post("/api/providers/openai/test", json={}).status_code == 400  # no key, no model
