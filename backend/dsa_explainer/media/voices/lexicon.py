"""Pronunciation lexicon: how data-structure words are read aloud.

Narration is written for the eye ("BFS", "O(n log n)", "a[i]", "dequeue"); a voice
model reads some of it wrongly ("deque" as "de-queue", "BST" as one word). These
rules rewrite the text that is *spoken* only; captions and transcripts keep the
words as written. Rules are ordered: notation first, then whole words.
"""

from __future__ import annotations

import re

VERSION = "1"  # part of the audio cache key: change it when a rule changes

# notation -> words (applied first, in order)
NOTATION: list[tuple[str, str]] = [
    (r"(\w+)\[\s*([^\]]+?)\s*\]", r"\1 of \2"),  # a[i] -> a of i, dist[B] -> dist of B
    (r"\b(\w+)\(\)", r"\1"),  # pop() -> pop
    (r"\b(\w+)\(([^()]*)\)", r"\1 \2"),  # push(7) -> push 7
    (r"->|→", " to "),
    (r"<=|≤", " at most "),
    (r">=|≥", " at least "),
    (r"(?<=\s)<(?=\s)", " is less than "),
    (r"(?<=\s)>(?=\s)", " is greater than "),
    (r"(?<=\s)=(?=\s)", " equals "),
    (r"∞", "infinity"),
    (r"\binf\b", "infinity"),
    (r"(?<=\d)\s+\+\s+(?=\d)", " plus "),
]

# whole words (case-sensitive where the case carries meaning) -> how to say them
WORDS: dict[str, str] = {
    "BFS": "B F S", "DFS": "D F S", "BST": "B S T", "DP": "D P", "DAG": "dag",
    "LIFO": "lie-foe", "FIFO": "fie-foe", "API": "A P I", "CPU": "C P U",
    "deque": "deck", "deques": "decks", "Deque": "Deck",
    "enqueue": "en-queue", "enqueues": "en-queues", "enqueued": "en-queued",
    "dequeue": "dee-queue", "dequeues": "dee-queues", "dequeued": "dee-queued",
    "Dijkstra": "Dike-struh", "Dijkstra's": "Dike-struh's",
    "heapify": "heap-ify", "min-heap": "min heap", "max-heap": "max heap",
    "quicksort": "quick sort", "mergesort": "merge sort", "heapsort": "heap sort",
    "argmin": "arg min", "len": "length",
    "i.e.": "that is", "e.g.": "for example",
}


def _big_o(match: re.Match) -> str:
    inner = match.group(1).strip()
    inner = re.sub(r"\^\s*2\b", " squared", inner)
    inner = re.sub(r"\^\s*(\w+)", r" to the \1", inner)
    inner = inner.replace("*", " times ").replace("+", " plus ")
    return "O of " + re.sub(r"\s+", " ", inner).strip()


_WORD = re.compile(r"(?<![\w-])(" + "|".join(re.escape(w) for w in sorted(WORDS, key=len, reverse=True))
                   + r")(?![\w-])")


def speakable(text: str) -> str:
    """The narration as the voice should read it."""
    text = re.sub(r"\bO\s*\(\s*([^)]*)\)", _big_o, text)
    for pattern, replacement in NOTATION:
        text = re.sub(pattern, replacement, text)
    text = _WORD.sub(lambda m: WORDS[m.group(1)], text)
    text = re.sub(r"[*_#`{}]", "", text)
    return re.sub(r"\s+", " ", text).strip()
