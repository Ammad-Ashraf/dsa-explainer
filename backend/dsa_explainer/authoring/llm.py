"""The language model, behind one small interface.

    llm.chat(messages, schema=None) -> reply text      (the planner, quiz writer and reviser use only this)
    llm.use(settings)                                  run a block with a given provider (one per job)

A Client holds everything about one provider configuration: its connection, its
rate-limit waits, whether the daily allowance forced the fallback model, and the
strongest JSON mode the provider accepted. Clients are cached per configuration,
so that state survives between jobs. No key is ever logged or shown: errors are
scrubbed of every key we know.

Check your settings with:  python -m dsa_explainer.authoring.llm
List the models your key can use:  python -m dsa_explainer.authoring.llm --models
"""

from __future__ import annotations

import contextlib
import contextvars
import json
import logging
import sys
import threading
import time
from dataclasses import dataclass

from openai import APIConnectionError, APIStatusError, BadRequestError, OpenAI, RateLimitError

from .. import config
from . import providers

logging.getLogger("httpx").setLevel(logging.WARNING)  # no line per API request in the console
RATE_LIMIT_WAITS = (10, 20, 30)  # seconds; free tiers allow only a few requests a minute
MODES = ("json_schema", "json_object", "none")


class LLMError(RuntimeError):
    """A problem the learner can fix: no key, a wrong key, an unreachable server, a rate limit."""


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    base_url: str
    api_key: str
    model: str
    fallback_model: str = ""
    structured: str = "json_object"

    @classmethod
    def from_dict(cls, data: dict) -> "LLMSettings":
        return cls(**{k: data[k] for k in ("provider", "base_url", "api_key", "model", "fallback_model", "structured")
                      if k in data})


def redact(text: str, secrets: list[str] | None = None) -> str:
    for secret in secrets if secrets is not None else providers.secrets():
        text = text.replace(secret, "[key]")
    return text


class Client:
    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings
        self.on_fallback = False  # set once the main model's daily allowance is used up
        self.mode = settings.structured if settings.structured in MODES else "json_object"
        self._openai: OpenAI | None = None

    def openai(self) -> OpenAI:
        if self._openai is None:
            self._openai = OpenAI(base_url=self.settings.base_url, api_key=self.settings.api_key or "not-needed",
                                  timeout=config.LLM_TIMEOUT, max_retries=1)  # a slow model should not wait 3 x the timeout
        return self._openai

    def model_in_use(self) -> str:
        return self.settings.fallback_model if self.on_fallback else self.settings.model

    def _create(self, **kwargs):
        """One API call. A per-minute rate limit: wait and try again. A daily limit: switch to the fallback model."""
        for wait in (*RATE_LIMIT_WAITS, None):
            kwargs["model"] = self.model_in_use()
            try:
                return self.openai().chat.completions.create(**kwargs)
            except RateLimitError as exc:
                details = f"{exc} {exc.body}".lower()  # the quota name, e.g. "...PerDay...", is in the body
                if self.settings.fallback_model and not self.on_fallback and "day" in details:
                    self.on_fallback = True
                    continue
                if wait is None:
                    raise LLMError("The language model's rate limit was reached (free tiers allow only a few "
                                   "requests per minute and per day). Wait a minute and try again, or choose another "
                                   "provider or model in Settings.") from exc
                time.sleep(wait)
            except APIConnectionError as exc:
                raise LLMError(f"Could not reach {self.settings.base_url}. Check the address and your connection"
                               + (" (is the local server running?)" if "127.0.0.1" in self.settings.base_url
                                  or "localhost" in self.settings.base_url else "") + ".") from exc
            except APIStatusError as exc:
                if exc.status_code in (401, 403):
                    raise LLMError("The provider refused the API key. Check it in Settings.") from exc
                if exc.status_code == 404:
                    raise LLMError(f"The provider does not know the model '{kwargs['model']}'. Pick another model "
                                   "in Settings.") from exc
                raise

    def chat(self, messages: list[dict], temperature: float | None = None, schema: dict | None = None,
             timeout: float | None = None) -> str:
        """One chat completion; returns the reply text. Uses the strongest JSON mode the provider accepts."""
        kwargs = {"messages": messages, "temperature": config.LLM_TEMPERATURE if temperature is None else temperature}
        if timeout is not None:
            kwargs["timeout"] = timeout
        while True:
            mode = self.mode if (self.mode != "json_schema" or schema) else "json_object"
            extra = {}
            if mode == "json_schema":
                extra["response_format"] = {"type": "json_schema",
                                            "json_schema": {"name": schema.get("title", "reply").lower(),
                                                            "schema": schema, "strict": False}}
            elif mode == "json_object":
                extra["response_format"] = {"type": "json_object"}
            try:
                reply = self._create(**kwargs, **extra)
            except BadRequestError as exc:
                text = str(exc).lower()
                if mode == "none" or not any(w in text for w in ("response_format", "json", "schema")):
                    raise
                # this provider (or model) lacks that JSON mode: step down once, for good
                self.mode = MODES[MODES.index(mode) + 1]
                continue
            return reply.choices[0].message.content or ""

    def list_models(self) -> list[str]:
        try:
            return sorted(m.id.removeprefix("models/") for m in self.openai().models.list())
        except APIConnectionError as exc:
            raise LLMError(f"Could not reach {self.settings.base_url}.") from exc
        except APIStatusError as exc:
            if exc.status_code in (401, 403):
                raise LLMError("The provider refused the API key.") from exc
            raise LLMError(f"The provider could not list its models ({exc.status_code}).") from exc

    def check(self) -> dict:
        started = time.perf_counter()
        reply = self.chat([{"role": "user", "content": 'Reply with the JSON object {"ok": true}.'}])
        ok = parse_json(reply).get("ok") is True
        return {"ok": ok, "model": self.model_in_use(), "seconds": round(time.perf_counter() - started, 2),
                "reply": reply.strip()[:200]}


# --- which client is in use ------------------------------------------------------------

_current: contextvars.ContextVar[Client | None] = contextvars.ContextVar("llm_client", default=None)
_clients: dict[LLMSettings, Client] = {}
_lock = threading.Lock()


def client_for(settings: LLMSettings) -> Client:
    with _lock:
        if settings not in _clients:
            _clients[settings] = Client(settings)
        return _clients[settings]


def active_settings() -> LLMSettings | None:
    data = providers.resolve()
    return LLMSettings.from_dict(data) if data else None


def configured() -> bool:
    return active_settings() is not None


def current() -> Client:
    client = _current.get()
    if client is None:
        settings = active_settings()
        if settings is None:
            raise LLMError("No language model is set up: add an API key in Settings (or in .env).")
        client = client_for(settings)
    return client


@contextlib.contextmanager
def use(settings: LLMSettings | None):
    """Run the block with this provider configuration (the active one if None)."""
    token = _current.set(client_for(settings) if settings else None)
    try:
        yield
    finally:
        _current.reset(token)


def chat(messages: list[dict], temperature: float | None = None, schema: dict | None = None,
         timeout: float | None = None) -> str:
    """One chat completion with the provider in use; returns the reply text."""
    try:
        return current().chat(messages, temperature, schema, timeout)
    except LLMError:
        raise
    except Exception as exc:  # never let a key reach a message or a log
        raise LLMError(redact(f"The language model call failed: {exc}")) from exc


def model_in_use() -> str:
    try:
        return current().model_in_use()
    except LLMError:
        return ""


def parse_json(text: str) -> dict:
    """The JSON object in a reply, tolerating ```json fences or text around it."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("the reply contains no JSON object")
    data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("the reply must be one JSON object")
    return data


def check() -> None:
    client = current()
    s = client.settings
    print(f"provider: {s.provider} ({s.base_url})\nmodel:    {s.model}"
          + (f" (fallback: {s.fallback_model})" if s.fallback_model else ""))
    result = client.check()
    print(f"{result['model']} replied in {result['seconds']:.1f} s: {result['reply']}")


if __name__ == "__main__":
    if "--models" in sys.argv:  # the model names this key can use
        print("\n".join(current().list_models()))
    else:
        check()
