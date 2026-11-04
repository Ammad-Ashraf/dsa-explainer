"""A thin client for any OpenAI-compatible chat API (Gemini, Groq, Claude,
OpenAI, Ollama...). Only planning and writing use the API; voice and video
run locally.

Check your settings with:  python -m dsa_explainer.llm
List the models your key can use:  python -m dsa_explainer.llm --models
"""

from __future__ import annotations

import json
import logging
import sys
import time

from openai import BadRequestError, OpenAI, RateLimitError

from . import config

logging.getLogger("httpx").setLevel(logging.WARNING)  # no line per API request in the console
_client: OpenAI | None = None
_json_mode = True  # turned off once if the provider rejects response_format
_on_fallback = False  # set once the main model's daily allowance is used up
RATE_LIMIT_WAITS = (10, 20, 30)  # seconds; free tiers allow only a few requests a minute


def client() -> OpenAI:
    global _client
    if _client is None:
        if not config.LLM_API_KEY:
            raise RuntimeError("No LLM_API_KEY: copy .env.example to .env and add your API key.")
        _client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY,
                         timeout=config.LLM_TIMEOUT, max_retries=2)
    return _client


def model_in_use() -> str:
    return config.LLM_FALLBACK_MODEL if _on_fallback else config.LLM_MODEL


def _create(**kwargs):
    """One API call. A per-minute rate limit: wait and try again. A daily limit: switch to the fallback model."""
    global _on_fallback
    for wait in (*RATE_LIMIT_WAITS, None):
        kwargs["model"] = model_in_use()
        try:
            return client().chat.completions.create(**kwargs)
        except RateLimitError as exc:
            details = f"{exc} {exc.body}".lower()  # the quota name, e.g. "...PerDay...", is in the body
            if config.LLM_FALLBACK_MODEL and not _on_fallback and "day" in details:
                _on_fallback = True  # the main model's daily allowance is used up
                continue
            if wait is None:
                raise RuntimeError("The language model's rate limit was reached (free tiers allow only a few "
                                   "requests per minute and per day). Wait a minute and try again, or use another "
                                   "key or provider in .env.") from exc
            time.sleep(wait)


def chat(messages: list[dict], temperature: float | None = None) -> str:
    """One chat completion; returns the reply text."""
    global _json_mode
    kwargs = {"model": config.LLM_MODEL, "messages": messages,
              "temperature": config.LLM_TEMPERATURE if temperature is None else temperature}
    if _json_mode:
        try:
            return _create(**kwargs, response_format={"type": "json_object"}).choices[0].message.content or ""
        except BadRequestError as exc:
            if "response_format" not in str(exc) and "json" not in str(exc).lower():
                raise
            _json_mode = False  # this provider has no JSON mode; the prompt still asks for JSON
    return _create(**kwargs).choices[0].message.content or ""


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
    print(f"provider: {config.LLM_BASE_URL}\nmodel:    {config.LLM_MODEL}"
          + (f" (fallback: {config.LLM_FALLBACK_MODEL})" if config.LLM_FALLBACK_MODEL else ""))
    started = time.perf_counter()
    reply = chat([{"role": "user", "content": 'Reply with the JSON object {"ok": true}.'}])
    print(f"{model_in_use()} replied in {time.perf_counter() - started:.1f} s: {reply.strip()[:200]}")


if __name__ == "__main__":
    if "--models" in sys.argv:  # the model names this key can use
        print("\n".join(sorted(m.id.removeprefix("models/") for m in client().models.list())))
    else:
        check()
