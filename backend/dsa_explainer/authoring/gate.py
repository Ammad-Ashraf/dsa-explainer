"""Topic gate: decide, before planning, whether a request is a topic the app can explain.

The planner can refuse an unsupported topic too, but only after a full planning
call: the whole catalogue in the prompt and the whole lesson schema to fill,
which can take minutes. The gate answers in two tiers:

  1. keywords: algorithms.candidates() matches the topic against every
     algorithm's keywords. A hit means the topic is in scope; no API call.
  2. a short classifier call, only when no keyword matched: the model sees the
     list of supported names and answers {"in_scope", "structure", "reason"}.
     A matched structure is passed on to the planner, so it gets the short
     single-algorithm prompt. The call goes to a light model (gate_model) at
     low reasoning effort, without rate-limit waits: about a second,
     against tens of seconds or minutes for a full planning call.

The gate fails open: if the classifier call errors, times out or replies with
something unreadable, the request goes on to the planner, whose own refusal is
still there. A network hiccup must never block a valid topic.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from .. import algorithms, config
from . import llm


@dataclass
class Verdict:
    in_scope: bool
    structure: str | None  # an algorithms.STRUCTURES name the topic is about, if one is clear
    reason: str
    source: str  # "keyword", "model", "fallback" (the classifier failed: let the planner decide) or "off"
    seconds: float = 0.0


SYSTEM_PROMPT = """You decide whether a learner's request can be turned into a lesson by DSA Explainer, an app that explains data structures and algorithms with animated videos.

Supported (name: title):
{catalog}

A request is in scope when it asks to learn, explain, show or trace one of these, in any wording or language, even without naming it (for example "how do I find the shortest route between cities" is dijkstra, "undo history in an editor" is stack). Anything else is out of scope: general knowledge, other computer-science topics that are not in the list, coding help, chit-chat.

Return ONLY a JSON object: {{"in_scope": true or false, "structure": "<one name from the list, or null>", "reason": "<at most 15 words>"}}"""


SCHEMA = {
    "title": "topic_gate",
    "type": "object",
    "properties": {
        "in_scope": {"type": "boolean"},
        "structure": {"type": ["string", "null"]},
        "reason": {"type": "string"},
    },
    "required": ["in_scope", "reason"],
}


def system_prompt() -> str:
    return SYSTEM_PROMPT.format(catalog="\n".join(f"- {cls.NAME}: {cls.TITLE}" for cls in algorithms.ALL))


def unsupported_message() -> str:
    """The message shown when a topic is out of scope, naming what is supported."""
    areas = [title.lower() for title in algorithms.CATEGORIES.values()]
    return ("This tool only explains data structures and algorithms: "
            + ", ".join(areas[:-1]) + " and " + areas[-1] + ". Try a topic such as bubble sort or Dijkstra.")


def gate_model() -> str | None:
    """The model that classifies: GATE_MODEL if set, else the provider's fallback model (usually a lighter,
    faster one, e.g. a "lite" model), else the main model (None). A yes/no question needs no big model."""
    if config.GATE_MODEL:
        return config.GATE_MODEL
    settings = llm.active_settings()
    return (settings.fallback_model or None) if settings else None


def check_topic(topic: str) -> Verdict:
    """Whether `topic` is something the planner can make a lesson about."""
    started = time.perf_counter()
    if not config.TOPIC_GATE:
        return Verdict(True, None, "the topic gate is off", "off")
    picked = algorithms.candidates(topic)
    if picked:
        return Verdict(True, picked[0].NAME if len(picked) == 1 else None,
                       "matched " + ", ".join(cls.NAME for cls in picked), "keyword",
                       time.perf_counter() - started)
    try:
        reply = llm.chat([{"role": "system", "content": system_prompt()},
                          {"role": "user", "content": f"Request: {topic.strip()}"}],
                         temperature=0, schema=SCHEMA, timeout=config.GATE_TIMEOUT, model=gate_model(), quick=True)
        data = llm.parse_json(reply)
        in_scope = data["in_scope"]
        if not isinstance(in_scope, bool):
            raise ValueError(f"in_scope is {in_scope!r}")
    except Exception as exc:  # noqa: BLE001 - any failure means: let the planner decide
        return Verdict(True, None, f"classifier unavailable ({type(exc).__name__})", "fallback",
                       time.perf_counter() - started)
    structure = data.get("structure")
    structure = algorithms.ALIASES.get(structure, structure) if isinstance(structure, str) else None
    if structure not in algorithms.STRUCTURES:
        structure = None
    return Verdict(in_scope, structure if in_scope else None, str(data.get("reason") or "")[:200], "model",
                   time.perf_counter() - started)
