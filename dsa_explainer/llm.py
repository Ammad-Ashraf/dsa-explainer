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

from openai import BadRequestError, OpenAI

from . import config

logging.getLogger("httpx").setLevel(logging.WARNING)  # no line per API request in the console
_client: OpenAI | None = None
_json_mode = True  # turned off once if the provider rejects response_format


def client() -> OpenAI:
    global _client
    if _client is None:
        if not config.LLM_API_KEY:
            raise RuntimeError("No LLM_API_KEY: copy .env.example to .env and add your API key.")
        _client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY,
                         timeout=config.LLM_TIMEOUT, max_retries=2)
    return _client


def chat(messages: list[dict], temperature: float | None = None) -> str:
    """One chat completion; returns the reply text."""
    global _json_mode
    kwargs = {"model": config.LLM_MODEL, "messages": messages,
              "temperature": config.LLM_TEMPERATURE if temperature is None else temperature}
    if _json_mode:
        try:
            reply = client().chat.completions.create(**kwargs, response_format={"type": "json_object"})
            return reply.choices[0].message.content or ""
        except BadRequestError as exc:
            if "response_format" not in str(exc) and "json" not in str(exc).lower():
                raise
            _json_mode = False  # this provider has no JSON mode; the prompt still asks for JSON
    reply = client().chat.completions.create(**kwargs)
    return reply.choices[0].message.content or ""


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
    print(f"provider: {config.LLM_BASE_URL}\nmodel:    {config.LLM_MODEL}")
    started = time.perf_counter()
    reply = chat([{"role": "user", "content": 'Reply with the JSON object {"ok": true}.'}])
    print(f"reply in {time.perf_counter() - started:.1f} s: {reply.strip()[:200]}")


if __name__ == "__main__":
    if "--models" in sys.argv:  # the model names this key can use
        print("\n".join(sorted(m.id.removeprefix("models/") for m in client().models.list())))
    else:
        check()
