"""What every algorithm simulator provides, and the helpers they share.

A simulator is the real data structure or algorithm. Every step of a lesson
plan is run on it, so the video always shows the true state, never what the
language model believes. Each simulator class declares:

  catalogue   NAME, TITLE, CATEGORY, DIFFICULTY, SUMMARY, DESCRIPTION, COMPLEXITY,
              PSEUDOCODE, KEYWORDS, REQUIRES, PRESETS, NOUN, VIEW
  simulation  OPS        operation name -> argument names (the planner may only use these)
              FACTS      named facts (top, size, ...) used to check narration and quiz answers
              FACT_WORDS extra narration words that name a fact ("pivot" -> "pivot")
              HELP       the reference the planner is given: initial data, operations, state format

and implements:
  run()       performs one operation and returns the element ids to highlight, in order;
              raises OpError when the operation is impossible (pop on an empty stack)
  state()     the plain state the planner must predict ("claimed_state")
  facts()     the current value of every fact
  snapshot()  the state with a stable id per element, for the renderer (its format is the VIEW's)
"""

from __future__ import annotations

import itertools

MAX_ITEMS = 7  # more than this does not fit on screen (arrays allow one more)

CATEGORIES = {
    "linear": "Linear structures",
    "trees": "Trees and heaps",
    "graphs": "Graphs",
    "sorting": "Sorting",
    "searching": "Searching",
    "hashing": "Hashing",
    "dp": "Dynamic programming",
}


class OpError(ValueError):
    """An operation that cannot run on the current state."""


def as_value(v):
    """5, "5" and 5.0 are the same value. Short words are allowed too."""
    if isinstance(v, (bool, list, dict)) or v is None:
        raise OpError(f"{v!r} is not a valid value; use a whole number or a short word")
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, str):
        v = v.strip()
        if v.lstrip("-").isdigit():
            v = int(v)
        elif not 0 < len(v) <= 6:
            raise OpError(f"{v!r} is not a valid value; use a whole number or a word of up to 6 letters")
    return v


def as_int(v, what: str = "value", low: int = -99, high: int = 999) -> int:
    v = as_value(v)
    if not isinstance(v, int):
        raise OpError(f"{what} must be a whole number, not {v!r}")
    if not low <= v <= high:
        raise OpError(f"{what} must be between {low} and {high}, not {v}")
    return v


def normalize(x):
    """Comparable form: numbers and strings become lower-case text."""
    if isinstance(x, dict):
        return {str(k): normalize(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [normalize(v) for v in x]
    if x is None:
        return None
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    return str(x).strip().lower()


def fact_text(value) -> str:
    """How a fact is written in narration and quiz answers."""
    if value is None:
        return "empty"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        return ", ".join(fact_text(v) if isinstance(v, bool) or v is None else str(v) for v in value) or "empty"
    return str(value)


def natural_key(label: str):
    """Sort node labels as numbers when they are numbers: 2 before 10."""
    label = str(label)
    return (0, int(label), "") if label.lstrip("-").isdigit() else (1, 0, label)


def flatten(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from flatten(v)
    elif isinstance(x, (list, tuple)):
        for v in x:
            yield from flatten(v)
    elif x is not None and not isinstance(x, bool):
        yield x


class Structure:
    # --- catalogue ---
    NAME = ""
    TITLE = ""
    CATEGORY = ""
    DIFFICULTY = "beginner"
    SUMMARY = ""
    DESCRIPTION = ""
    COMPLEXITY: dict[str, str] = {}
    PSEUDOCODE: tuple[str, ...] = ()
    KEYWORDS: tuple[str, ...] = ()
    REQUIRES = ""
    PRESETS: dict[str, object] = {}
    NOUN = "items"
    VIEW = ""
    # --- simulation ---
    OPS: dict[str, tuple[str, ...]] = {}
    FACTS: tuple[str, ...] = ()
    FACT_WORDS: dict[str, str] = {}
    HELP = ""

    def __init__(self) -> None:
        self._ids = itertools.count(1)

    def new_id(self) -> int:
        return next(self._ids)

    def run(self, op: str, args: dict | None = None) -> list:
        args = args or {}
        if op not in self.OPS:
            raise OpError(f"'{op}' is not an operation of {self.TITLE or self.NAME}; use one of: {', '.join(self.OPS)}")
        missing = [a for a in self.OPS[op] if a not in args]
        if missing:
            raise OpError(f"{op} needs the argument(s): {', '.join(missing)}")
        return getattr(self, "op_" + op)(*(args[a] for a in self.OPS[op]))

    def matches(self, claimed) -> bool:
        return normalize(claimed) == normalize(self.state())

    def values(self) -> set[str]:
        """Every value in the structure, as text (narration may mention these)."""
        return {normalize(v) for v in flatten(self.state())}

    def state(self):
        raise NotImplementedError

    def facts(self) -> dict:
        raise NotImplementedError

    def snapshot(self) -> dict:
        raise NotImplementedError

    @classmethod
    def info(cls) -> dict:
        """The catalogue entry the web app shows."""
        return {
            "id": cls.NAME, "title": cls.TITLE, "category": cls.CATEGORY,
            "category_title": CATEGORIES.get(cls.CATEGORY, cls.CATEGORY), "difficulty": cls.DIFFICULTY,
            "summary": cls.SUMMARY, "description": cls.DESCRIPTION, "complexity": dict(cls.COMPLEXITY),
            "pseudocode": list(cls.PSEUDOCODE), "requires": cls.REQUIRES, "presets": dict(cls.PRESETS),
            "operations": {name: list(args) for name, args in cls.OPS.items()}, "facts": list(cls.FACTS),
            "view": cls.VIEW, "noun": cls.NOUN,
        }
