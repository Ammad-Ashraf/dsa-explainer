"""Wrong answers worth offering: what a learner gets by making a typical mistake.

A good wrong option is not random; it is the answer to a slightly wrong
reading of the question: forgetting the last operation, running it twice,
doing the last two in the wrong order, or treating a queue as a stack. Each
mistake is *simulated* on the real data structure, so its answer is exact, and
an option is only kept when it differs from the true answer. The reason is kept
too, so the app can say why an option is wrong.

Everything here is computed; the language model is not involved.
"""

from __future__ import annotations

import re

from .. import algorithms
from ..algorithms import OpError, build, fact_text
from ..core.lesson import Lesson, Op, Question

# Structures learners mix up: (theirs, the one they think of) -> operation and fact names translated across.
CONFUSIONS: dict[tuple[str, str], dict] = {
    ("queue", "stack"): {"ops": {"enqueue": "push", "dequeue": "pop", "peek": "peek"},
                         "facts": {"front": "top", "rear": "top", "size": "size", "items": "items"}},
    ("stack", "queue"): {"ops": {"push": "enqueue", "pop": "dequeue", "peek": "peek"},
                         "facts": {"top": "front", "size": "size", "items": "items"}},
    ("bfs", "dfs"): {"ops": {"bfs_step": "dfs_step"}, "facts": {"current": "current", "visited": "visited",
                                                                 "bfs_order": "dfs_order", "size": "size"}},
    ("dfs", "bfs"): {"ops": {"dfs_step": "bfs_step"}, "facts": {"current": "current", "visited": "visited",
                                                                 "dfs_order": "bfs_order", "size": "size"}},
    ("bubble_sort", "selection_sort"): {"ops": {"bubble_pass": "select_next"}, "facts": {"items": "items"}},
    ("selection_sort", "insertion_sort"): {"ops": {"select_next": "insert_next"}, "facts": {"items": "items"}},
    ("insertion_sort", "selection_sort"): {"ops": {"insert_next": "select_next"}, "facts": {"items": "items"}},
}

# The fact a built-in question asks about, per algorithm (default: the first fact of its strip).
QUIZ_FACTS = {
    "bubble_sort": "items", "insertion_sort": "items", "selection_sort": "items", "merge_sort": "items",
    "quick_sort": "items", "heap_sort": "items", "linear_search": "index", "binary_search": "mid",
    "bfs": "visited", "dfs": "visited", "topological_sort": "order", "dijkstra": "distances",
    "tree_traversal": "visited", "fibonacci": "value", "coin_change": "value", "hash_table": "items",
    "linked_list": "items", "deque": "items",
}


def answer(structure: str, start, ops: list[Op], ask: str) -> str:
    """The value of `ask` after running `ops` from `start` (raises OpError)."""
    ds = build(structure, start)
    for op in ops:
        ds.run(op.name, op.args)
    facts = ds.facts()
    if ask not in facts:
        raise OpError(f"{structure} has no fact {ask}")
    return fact_text(facts[ask])


def same_answer(a: str, b: str) -> bool:
    return re.sub(r"[\s\[\]'\"]", "", a).lower() == re.sub(r"[\s\[\]'\"]", "", b).lower()


def mistakes(lesson: Lesson, q: Question) -> dict[str, str]:
    """{wrong answer: the mistake that gives it}, every one simulated and different from the true answer."""
    start = q.start if q.start is not None else lesson.initial
    structure = algorithms.resolve(lesson.structure)
    ops, ask = list(q.ops), q.ask
    truth = answer(structure, start, ops, ask)
    variants: list[tuple[str, str, list[Op], str]] = []
    if ops:
        variants.append((structure, "forgetting the last operation", ops[:-1], ask))
        variants.append((structure, "running the last operation twice", ops + [ops[-1]], ask))
        variants.append((structure, "reading the value before any operation ran", [], ask))
    if len(ops) >= 2 and ops[-1] != ops[-2]:
        variants.append((structure, "doing the last two operations in the wrong order", ops[:-2] + [ops[-1], ops[-2]],
                         ask))
    for (mine, other), table in CONFUSIONS.items():
        if mine == structure and ask in table["facts"] and all(o.name in table["ops"] for o in ops):
            translated = [Op(name=table["ops"][o.name], args=_args(other, table["ops"][o.name], o.args)) for o in ops]
            title = algorithms.get(other).TITLE.lower()
            mine_title = algorithms.get(structure).TITLE.lower()
            variants.append((other, f"treating the {mine_title} as a {title}", translated, table["facts"][ask]))
    found: dict[str, str] = {}
    for name, why, run, fact in variants:
        try:
            value = answer(name, start, run, fact)
        except (OpError, TypeError, ValueError):
            continue  # the mistaken sequence cannot even run: no option from it
        if value in ("-", "empty") and truth not in ("-", "empty"):
            continue  # "nothing yet" is not a believable answer to a question about the end of the lesson
        if not same_answer(value, truth) and not any(same_answer(value, v) for v in found):
            found[value] = why
    return found


def _args(structure: str, op: str, args: dict) -> dict:
    """Arguments renamed for the other structure's operation (both take one value, or none)."""
    names = algorithms.get(structure).OPS[op]
    return dict(zip(names, args.values()))


def near_misses(truth: str) -> dict[str, str]:
    """For a number: one more and one less (still verified wrong, but not a simulated mistake)."""
    if not re.fullmatch(r"-?\d+", truth):
        return {}
    n = int(truth)
    return {str(v): "off by one" for v in (n + 1, n - 1) if v >= 0}


def with_options(lesson: Lesson, q: Question, keep: list[str] | None = None, size: int = 4) -> Question:
    """The question with its options rebuilt: the true answer, the given options that are still wrong, then
    simulated mistakes, then near misses; why_wrong explains the simulated ones."""
    start = q.start if q.start is not None else lesson.initial
    truth = answer(algorithms.resolve(lesson.structure), start, q.ops, q.ask)
    reasons = {**near_misses(truth), **mistakes(lesson, q)}
    wrong: list[str] = []
    for option in (keep or []) + list(reasons):
        if not same_answer(option, truth) and not any(same_answer(option, w) for w in wrong):
            wrong.append(option)
    options = [truth] + wrong[: size - 1]
    if len(options) < 2:
        raise OpError("no wrong answer could be simulated for this question")
    options.sort(key=lambda o: (len(o), o))  # a stable order that does not give the answer away
    q = q.model_copy(update={"options": options, "answer": truth})
    q.why_wrong = {o: reasons[o] for o in options
                   if o in reasons and not same_answer(o, truth) and reasons[o] != "off by one"}
    return q
