"""The algorithm registry: every data structure and algorithm the pipeline can explain.

The planner's prompt, the verifier's narration checks, the quiz writer, the
renderer and the web app's library all read from here, so adding an algorithm
means adding one simulator class (in the module of its family, or a new one),
listing it in ALL, giving its VIEW a drawer in media/views, and adding tests
and a saved plan. See CONTRIBUTING.md.
"""

from __future__ import annotations

import re

from .arrays import BinarySearch, BubbleSort, InsertionSort, LinearSearch, MergeSort, QuickSort, SelectionSort
from .base import (
    CATEGORIES,
    MAX_ITEMS,
    OpError,
    Structure,
    as_value,
    fact_text,
    natural_key,
    normalize,
)
from .dp import CoinChange, Fibonacci
from .graphs import BFS, DFS, Dijkstra, TopologicalSort
from .hashing import HashTable
from .linear import Deque, LinkedList, Queue, Stack
from .trees import BST, HeapSort, MinHeap, TreeTraversal

ALL: tuple[type[Structure], ...] = (
    Stack, Queue, Deque, LinkedList,
    BST, TreeTraversal, MinHeap,
    BFS, DFS, Dijkstra, TopologicalSort,
    BubbleSort, InsertionSort, SelectionSort, MergeSort, QuickSort, HeapSort,
    LinearSearch, BinarySearch,
    HashTable,
    Fibonacci, CoinChange,
)
STRUCTURES: dict[str, type[Structure]] = {cls.NAME: cls for cls in ALL}
ALIASES = {"graph": "bfs"}  # lessons made before the registry called BFS "graph"
DISPLAY_NAMES = {**{name: cls.TITLE for name, cls in STRUCTURES.items()},
                 **{old: STRUCTURES[new].TITLE for old, new in ALIASES.items()}}
Graph = BFS  # older name

# Narration words every lesson may use to state a fact; algorithms add their own in FACT_WORDS.
SHARED_FACT_WORDS = {
    "top": "top", "front": "front", "rear": "rear", "back": "rear", "head": "head", "tail": "tail",
    "root": "root", "size": "size", "length": "size", "current node": "current",
    "minimum": "min", "maximum": "max",
}


def resolve(name: str) -> str:
    name = ALIASES.get(name, name)
    if name not in STRUCTURES:
        raise OpError(f"unknown structure '{name}'; use one of: {', '.join(STRUCTURES)}")
    return name


def get(name: str) -> type[Structure]:
    return STRUCTURES[resolve(name)]


def build(name: str, initial) -> Structure:
    return get(name)(initial)


def fact_words() -> dict[str, str]:
    words = dict(SHARED_FACT_WORDS)
    for cls in ALL:
        words.update(cls.FACT_WORDS)
    return words


def candidates(topic: str) -> list[type[Structure]]:
    """The algorithms a topic is most likely about, by keyword; empty if none match."""
    text = topic.lower()
    scores = {}
    for cls in ALL:
        hits = sum(1 for kw in cls.KEYWORDS + (cls.NAME.replace("_", " "),)
                   if re.search(r"(?<![a-z])" + re.escape(kw) + r"(?![a-z])", text))
        if hits:
            scores[cls] = hits
    best = max(scores.values(), default=0)
    return [cls for cls in ALL if scores.get(cls, 0) == best and best > 0]


def catalog(names: list[str] | None = None) -> str:
    """The reference given to the language model (all algorithms, or just `names`)."""
    chosen = [get(n) for n in names] if names else list(ALL)
    return "\n".join("- " + cls.HELP for cls in chosen)


def info() -> list[dict]:
    return [cls.info() for cls in ALL]


__all__ = [
    "ALL", "ALIASES", "BFS", "BST", "CATEGORIES", "DISPLAY_NAMES", "MAX_ITEMS", "STRUCTURES", "BinarySearch",
    "BubbleSort", "CoinChange", "DFS", "Deque", "Dijkstra", "Fibonacci", "Graph", "HashTable", "HeapSort",
    "InsertionSort", "LinearSearch", "LinkedList", "MergeSort", "MinHeap", "OpError", "Queue", "QuickSort",
    "SelectionSort", "Stack", "Structure", "TopologicalSort", "TreeTraversal", "as_value", "build", "candidates",
    "catalog", "fact_text", "fact_words", "get", "info", "natural_key", "normalize", "resolve",
]
