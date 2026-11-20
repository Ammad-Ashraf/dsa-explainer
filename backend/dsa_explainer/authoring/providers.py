"""Language-model providers: presets, and the learner's own saved choices.

Every preset speaks the OpenAI chat-completions API (most providers offer it,
including Anthropic, Gemini, Groq, OpenRouter and local servers such as Ollama
and LM Studio), so one client covers them all; `llm.Client` is the single place
to add a native adapter later.

The learner's keys and model choices live in settings.json under "llm":
    {"active": "gemini", "providers": {"gemini": {"api_key": "...", "model": "...", "fallback_model": "..."}}}
They never leave this machine except to the provider they belong to, and the
API only ever returns a short hint of a key, never the key.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .. import config, settings


@dataclass(frozen=True)
class Preset:
    id: str
    name: str
    base_url: str
    default_model: str
    fallback_model: str = ""
    key_url: str = ""
    needs_key: bool = True
    local: bool = False  # runs on this machine: no key, nothing leaves the computer
    structured: str = "json_object"  # strongest JSON mode known to work: json_schema | json_object | none
    notes: str = ""


PRESETS: dict[str, Preset] = {p.id: p for p in (
    Preset("gemini", "Google Gemini", "https://generativelanguage.googleapis.com/v1beta/openai/",
           "gemini-3.5-flash", "gemini-3.5-flash-lite", "https://aistudio.google.com/apikey", structured="json_schema",
           notes="Free tier: a few requests a minute and about 20 a day per model; the fallback model takes over "
                 "when the daily allowance runs out."),
    Preset("anthropic", "Anthropic Claude", "https://api.anthropic.com/v1/", "claude-sonnet-5-5",
           "claude-haiku-5-5", "https://console.anthropic.com/settings/keys",
           notes="Paid. Very reliable at long structured plans."),
    Preset("openai", "OpenAI", "https://api.openai.com/v1", "", "", "https://platform.openai.com/api-keys",
           structured="json_schema", notes="Paid. Pick a model from the list after testing the key."),
    Preset("groq", "Groq", "https://api.groq.com/openai/v1", "openai/gpt-oss-120b", "",
           "https://console.groq.com/keys", notes="Free tier with fast open-weight models."),
    Preset("openrouter", "OpenRouter", "https://openrouter.ai/api/v1", "", "", "https://openrouter.ai/keys",
           notes="One key for many providers' models. Pick a model from the list."),
    Preset("ollama", "Ollama (on this computer)", "http://127.0.0.1:11434/v1", "qwen2.5:7b-instruct", "",
           "https://ollama.com/download", needs_key=False, local=True,
           notes="No key and no internet. Slower, and small models fail verification more often."),
    Preset("lmstudio", "LM Studio (on this computer)", "http://127.0.0.1:1234/v1", "", "",
           "https://lmstudio.ai", needs_key=False, local=True, notes="Start LM Studio's local server first."),
    Preset("custom", "Other OpenAI-compatible API", "", "", "", needs_key=False,
           notes="Any server that speaks the OpenAI chat-completions API."),
)}

FIELDS = ("api_key", "model", "fallback_model", "base_url")


class ProviderError(ValueError):
    pass


def _saved() -> dict:
    data = settings.raw().get("llm") or {}
    data.setdefault("active", None)
    data.setdefault("providers", {})
    return data


def key_hint(key: str) -> str:
    return f"…{key[-4:]}" if len(key) >= 8 else ("set" if key else "")


def env_settings() -> dict | None:
    """The provider configured in .env, used when none was chosen in the app."""
    if not config.LLM_API_KEY:
        return None
    same = next((p for p in PRESETS.values() if p.base_url and p.base_url.rstrip("/") == config.LLM_BASE_URL.rstrip("/")),
                None)
    return {"provider": "env", "base_url": config.LLM_BASE_URL, "api_key": config.LLM_API_KEY,
            "model": config.LLM_MODEL, "fallback_model": config.LLM_FALLBACK_MODEL,
            "structured": same.structured if same else "json_object"}


def resolve(provider_id: str | None = None, overrides: dict | None = None) -> dict | None:
    """Everything needed to call a provider: the preset, the saved choices, then `overrides`.
    None when nothing usable is configured."""
    saved = _saved()
    provider_id = provider_id or saved["active"]
    if provider_id in (None, "env"):
        return env_settings()
    preset = PRESETS.get(provider_id)
    if preset is None:
        raise ProviderError(f"unknown provider '{provider_id}'")
    chosen = {**saved["providers"].get(provider_id, {}), **{k: v for k, v in (overrides or {}).items() if v}}
    base_url = chosen.get("base_url") or preset.base_url
    model = chosen.get("model") or preset.default_model
    key = chosen.get("api_key", "")
    if not base_url or not model or (preset.needs_key and not key):
        return None
    return {"provider": provider_id, "base_url": base_url, "api_key": key or "not-needed", "model": model,
            "fallback_model": chosen.get("fallback_model", preset.fallback_model) or "",
            "structured": preset.structured}


def describe() -> dict:
    """Presets and saved choices for the settings page: never the keys themselves."""
    saved = _saved()
    providers = []
    for preset in PRESETS.values():
        mine = saved["providers"].get(preset.id, {})
        providers.append({
            **asdict(preset),
            "saved": {"model": mine.get("model", ""), "fallback_model": mine.get("fallback_model", ""),
                      "base_url": mine.get("base_url", ""), "key_set": bool(mine.get("api_key")),
                      "key_hint": key_hint(mine.get("api_key", ""))},
            "ready": resolve(preset.id) is not None,
        })
    env = env_settings()
    return {
        "active": saved["active"] or ("env" if env else None),
        "env": None if env is None else {"base_url": env["base_url"], "model": env["model"],
                                         "fallback_model": env["fallback_model"], "key_hint": key_hint(env["api_key"])},
        "providers": providers,
    }


def save(provider_id: str, changes: dict, activate: bool = False) -> dict:
    if provider_id not in PRESETS:
        raise ProviderError(f"unknown provider '{provider_id}'")
    unknown = set(changes) - set(FIELDS)
    if unknown:
        raise ProviderError(f"unknown field(s): {', '.join(sorted(unknown))}")
    for name, value in changes.items():
        if not isinstance(value, str) or len(value) > 500:
            raise ProviderError(f"{name} must be text of at most 500 characters")
    base_url = changes.get("base_url")
    if base_url and not base_url.startswith(("http://", "https://")):
        raise ProviderError("the base URL must start with http:// or https://")
    data = _saved()
    mine = data["providers"].setdefault(provider_id, {})
    for name, value in changes.items():
        value = value.strip()
        if value:
            mine[name] = value
        else:
            mine.pop(name, None)  # an empty value clears the field (and a key)
    if activate:
        data["active"] = provider_id
    settings.update_section("llm", data)
    return describe()


def activate(provider_id: str | None) -> dict:
    if provider_id not in (None, "env") and provider_id not in PRESETS:
        raise ProviderError(f"unknown provider '{provider_id}'")
    data = _saved()
    data["active"] = None if provider_id == "env" else provider_id
    settings.update_section("llm", data)
    return describe()


def secrets() -> list[str]:
    """Every key we know, so error messages can be scrubbed of them."""
    keys = [p.get("api_key", "") for p in _saved()["providers"].values()]
    return [k for k in keys + [config.LLM_API_KEY] if k and len(k) >= 6]
