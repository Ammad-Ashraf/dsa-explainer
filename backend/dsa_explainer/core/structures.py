"""The real data structures. Every step of a lesson plan is run here, so the
video always shows the true state, never what the language model believes.

Each structure offers:
  OPS         operation name -> argument names (the planner may only use these)
  run()       performs one operation and returns the ids to highlight, in order;
              raises OpError when the operation is impossible (pop on an empty stack)
  state()     the plain state the planner must predict ("claimed_state")
  facts()     named facts (top, size, ...) used to check narration and quiz answers
  snapshot()  the state with a stable id per element, for the animation
"""

from __future__ import annotations

import itertools

MAX_ITEMS = 7  # more than this does not fit on screen


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


def normalize(x):
    """Comparable form: numbers and strings become lower-case text."""
    if isinstance(x, dict):
        return {str(k): normalize(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [normalize(v) for v in x]
    if x is None:
        return None
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    return str(x).strip().lower()


def fact_text(value) -> str:
    """How a fact is written in narration and quiz answers."""
    if value is None:
        return "empty"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value) if value else "empty"
    return str(value)


def natural_key(label: str):
    """Sort node labels as numbers when they are numbers: 2 before 10."""
    return (0, int(label), "") if label.lstrip("-").isdigit() else (1, 0, label)


class Structure:
    NAME = ""
    OPS: dict[str, tuple[str, ...]] = {}
    FACTS: tuple[str, ...] = ()
    HELP = ""

    def __init__(self) -> None:
        self._ids = itertools.count(1)

    def new_id(self) -> int:
        return next(self._ids)

    def run(self, op: str, args: dict | None = None) -> list:
        args = args or {}
        if op not in self.OPS:
            raise OpError(f"'{op}' is not an operation of a {self.NAME}; use one of: {', '.join(self.OPS)}")
        missing = [a for a in self.OPS[op] if a not in args]
        if missing:
            raise OpError(f"{op} needs the argument(s): {', '.join(missing)}")
        return getattr(self, "op_" + op)(*(args[a] for a in self.OPS[op]))

    def matches(self, claimed) -> bool:
        return normalize(claimed) == normalize(self.state())

    def values(self) -> set[str]:
        """Every value in the structure, as text (narration may mention these)."""
        return {normalize(v) for v in _flatten(self.state())}

    def state(self):
        raise NotImplementedError

    def facts(self) -> dict:
        raise NotImplementedError

    def snapshot(self) -> dict:
        raise NotImplementedError


def _flatten(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from _flatten(v)
    elif isinstance(x, (list, tuple)):
        for v in x:
            yield from _flatten(v)
    elif x is not None:
        yield x


# --- linear structures: stack, queue, linked list -----------------------------


class _Linear(Structure):
    """A row of (id, value) items. Index 0 is the bottom / front / head."""

    def __init__(self, initial) -> None:
        super().__init__()
        if not isinstance(initial, list):
            raise OpError(f"initial data for a {self.NAME} must be a list of values")
        self.items: list[tuple[int, object]] = []
        for v in initial:
            self._add(len(self.items), v)

    def _add(self, index: int, value) -> int:
        if len(self.items) >= MAX_ITEMS:
            raise OpError(f"keep at most {MAX_ITEMS} items so the picture stays readable")
        item = (self.new_id(), as_value(value))
        self.items.insert(index, item)
        return item[0]

    def _need_items(self, op: str) -> None:
        if not self.items:
            raise OpError(f"cannot {op}: the {self.NAME.replace('_', ' ')} is empty")

    def state(self):
        return [v for _, v in self.items]

    def snapshot(self) -> dict:
        return {"items": [list(item) for item in self.items]}


class Stack(_Linear):
    NAME = "stack"
    OPS = {"push": ("value",), "pop": (), "peek": ()}
    FACTS = ("top", "size", "items")
    HELP = (
        "stack: initial = list of values from bottom to top, e.g. [4, 9]. "
        "ops: push(value), pop(), peek(). state = list from bottom to top. "
        "facts: top, size, items (bottom to top)."
    )

    def op_push(self, value):
        return [self._add(len(self.items), value)]

    def op_pop(self):
        self._need_items("pop")
        return [self.items.pop()[0]]

    def op_peek(self):
        self._need_items("peek")
        return [self.items[-1][0]]

    def facts(self) -> dict:
        return {"top": self.items[-1][1] if self.items else None, "size": len(self.items), "items": self.state()}


class Queue(_Linear):
    NAME = "queue"
    OPS = {"enqueue": ("value",), "dequeue": (), "peek": ()}
    FACTS = ("front", "rear", "size", "items")
    HELP = (
        "queue: initial = list of values from front to rear, e.g. [3, 8]. "
        "ops: enqueue(value) adds at the rear, dequeue() removes from the front, peek() reads the front. "
        "state = list from front to rear. facts: front, rear, size, items (front to rear)."
    )

    def op_enqueue(self, value):
        return [self._add(len(self.items), value)]

    def op_dequeue(self):
        self._need_items("dequeue")
        return [self.items.pop(0)[0]]

    def op_peek(self):
        self._need_items("peek")
        return [self.items[0][0]]

    def facts(self) -> dict:
        first = self.items[0][1] if self.items else None
        last = self.items[-1][1] if self.items else None
        return {"front": first, "rear": last, "size": len(self.items), "items": self.state()}


class LinkedList(_Linear):
    NAME = "linked_list"
    OPS = {
        "insert_head": ("value",),
        "insert_tail": ("value",),
        "insert_at": ("index", "value"),
        "delete": ("value",),
        "search": ("value",),
    }
    FACTS = ("head", "tail", "size", "items")
    HELP = (
        "linked_list (singly linked): initial = list of values from head to tail, e.g. [3, 8, 12]. "
        "ops: insert_head(value), insert_tail(value), insert_at(index, value) with index 0 = head, "
        "delete(value) removes the first node holding value, search(value) walks from the head. "
        "state = list from head to tail. facts: head, tail, size, items (head to tail)."
    )

    def _path(self, upto: int) -> list[int]:
        return [iid for iid, _ in self.items[:upto]]

    def op_insert_head(self, value):
        return [self._add(0, value)]

    def op_insert_tail(self, value):
        # no tail pointer: walk to the last node first
        return self._path(len(self.items)) + [self._add(len(self.items), value)]

    def op_insert_at(self, index, value):
        if isinstance(index, str) and index.strip().isdigit():
            index = int(index)
        if not isinstance(index, int) or not 0 <= index <= len(self.items):
            raise OpError(f"index must be a whole number from 0 to {len(self.items)}, not {index!r}")
        return self._path(index) + [self._add(index, value)]

    def op_delete(self, value):
        value = as_value(value)
        for pos, (_, v) in enumerate(self.items):
            if v == value:
                path = self._path(pos + 1)
                del self.items[pos]
                return path
        raise OpError(f"{value} is not in the list, so it cannot be deleted")

    def op_search(self, value):
        value = as_value(value)
        for pos, (_, v) in enumerate(self.items):
            if v == value:
                return self._path(pos + 1)
        return self._path(len(self.items))  # not found: every node was checked

    def facts(self) -> dict:
        head = self.items[0][1] if self.items else None
        tail = self.items[-1][1] if self.items else None
        return {"head": head, "tail": tail, "size": len(self.items), "items": self.state()}


# --- binary search tree -------------------------------------------------------


class _Node:
    def __init__(self, nid: int, value: int) -> None:
        self.id, self.value = nid, value
        self.left: _Node | None = None
        self.right: _Node | None = None


def _norm_tree(t):
    if not isinstance(t, dict):
        return None if t in (None, [], {}) else normalize(t)
    return {"value": normalize(t.get("value")), "left": _norm_tree(t.get("left")), "right": _norm_tree(t.get("right"))}


class BST(Structure):
    NAME = "bst"
    OPS = {"insert": ("value",), "search": ("value",), "delete": ("value",)}
    FACTS = ("root", "size", "min", "max", "inorder", "preorder", "postorder", "levelorder")
    HELP = (
        "bst (binary search tree, no duplicates): initial = list of whole numbers inserted in that order, "
        "e.g. [8, 3, 10]. ops: insert(value), search(value), delete(value); a node with two children is "
        "replaced by its in-order successor (the smallest value in its right subtree). "
        'state = nested object {"value": 8, "left": {...} or null, "right": {...} or null}, null if empty. '
        "facts: root, size, min, max, inorder, preorder, postorder, levelorder."
    )

    def __init__(self, initial) -> None:
        super().__init__()
        if not isinstance(initial, list):
            raise OpError("initial data for a bst must be a list of whole numbers")
        self.root: _Node | None = None
        for v in initial:
            self.op_insert(v)

    @staticmethod
    def _number(v) -> int:
        v = as_value(v)
        if not isinstance(v, int):
            raise OpError(f"bst values must be whole numbers, not {v!r}")
        return v

    def _find(self, value: int):
        """The nodes compared while looking for value, its parent, and the node (or None)."""
        path, parent, node = [], None, self.root
        while node is not None and node.value != value:
            path.append(node)
            parent, node = node, (node.left if value < node.value else node.right)
        if node is not None:
            path.append(node)
        return path, parent, node

    def op_insert(self, value):
        value = self._number(value)
        if len(self._inorder(self.root)) >= MAX_ITEMS:
            raise OpError(f"keep at most {MAX_ITEMS} nodes so the picture stays readable")
        path, parent, node = self._find(value)
        if node is not None:
            raise OpError(f"{value} is already in the tree (this BST has no duplicates)")
        new = _Node(self.new_id(), value)
        if parent is None:
            self.root = new
        elif value < parent.value:
            parent.left = new
        else:
            parent.right = new
        return [n.id for n in path] + [new.id]

    def op_search(self, value):
        path, _, _ = self._find(self._number(value))
        return [n.id for n in path]

    def op_delete(self, value):
        value = self._number(value)
        path, parent, node = self._find(value)
        if node is None:
            raise OpError(f"{value} is not in the tree, so it cannot be deleted")
        focus = [n.id for n in path]
        if node.left is not None and node.right is not None:
            # copy the in-order successor into this node, then remove the successor
            succ_parent, succ = node, node.right
            while succ.left is not None:
                focus.append(succ.id)
                succ_parent, succ = succ, succ.left
            focus.append(succ.id)
            node.value = succ.value
            parent, node = succ_parent, succ
        child = node.left if node.left is not None else node.right
        if parent is None:
            self.root = child
        elif parent.left is node:
            parent.left = child
        else:
            parent.right = child
        return focus

    def _inorder(self, n):
        return self._inorder(n.left) + [n.value] + self._inorder(n.right) if n else []

    def _preorder(self, n):
        return [n.value] + self._preorder(n.left) + self._preorder(n.right) if n else []

    def _postorder(self, n):
        return self._postorder(n.left) + self._postorder(n.right) + [n.value] if n else []

    def _levelorder(self):
        out, level = [], [self.root] if self.root else []
        while level:
            out += [n.value for n in level]
            level = [c for n in level for c in (n.left, n.right) if c is not None]
        return out

    def _tree(self, n):
        return None if n is None else {"value": n.value, "left": self._tree(n.left), "right": self._tree(n.right)}

    def state(self):
        return self._tree(self.root)

    def matches(self, claimed) -> bool:
        return _norm_tree(claimed) == _norm_tree(self.state())

    def facts(self) -> dict:
        ino = self._inorder(self.root)
        return {
            "root": self.root.value if self.root else None,
            "size": len(ino),
            "min": ino[0] if ino else None,
            "max": ino[-1] if ino else None,
            "inorder": ino,
            "preorder": self._preorder(self.root),
            "postorder": self._postorder(self.root),
            "levelorder": self._levelorder(),
        }

    def snapshot(self) -> dict:
        nodes = {}

        def add(n):
            if n is not None:
                nodes[n.id] = [n.value, n.left.id if n.left else None, n.right.id if n.right else None]
                add(n.left)
                add(n.right)

        add(self.root)
        return {"root": self.root.id if self.root else None, "nodes": nodes}


# --- graph, breadth-first search ---------------------------------------------


def _label(x) -> str:
    s = str(x).strip()
    if not 0 < len(s) <= 3:
        raise OpError(f"node label {x!r} must be 1 to 3 characters")
    return s


class Graph(Structure):
    NAME = "graph"
    OPS = {"bfs_step": ()}
    FACTS = ("current", "queue", "visited", "bfs_order", "size")
    HELP = (
        'graph (breadth-first search): initial = {"edges": [["A", "B"], ["A", "C"]], "start": "A", '
        '"directed": false}, short node labels. ops: bfs_step() takes the node at the front of the queue, '
        "marks it visited, then adds its neighbours that are neither visited nor already queued to the back "
        "of the queue, in alphabetical (or numeric) order. Before the first step the queue holds only the "
        'start node. state = {"current": the node just taken, "queue": [front ... back], "visited": [nodes '
        'in the order they were taken]}. facts: current, queue, visited, bfs_order (the full BFS order), '
        "size (number of nodes)."
    )

    def __init__(self, initial) -> None:
        super().__init__()
        if not isinstance(initial, dict) or "edges" not in initial or "start" not in initial:
            raise OpError('initial data for a graph must be {"edges": [["A", "B"], ...], "start": "A"}')
        self.directed = bool(initial.get("directed", False))
        self.adj: dict[str, set[str]] = {}
        for n in initial.get("nodes") or []:
            self.adj.setdefault(_label(n), set())
        for e in initial["edges"]:
            if not isinstance(e, (list, tuple)) or len(e) != 2:
                raise OpError(f'edge {e!r} must be a pair like ["A", "B"]')
            a, b = _label(e[0]), _label(e[1])
            self.adj.setdefault(a, set()).add(b)
            self.adj.setdefault(b, set())
            if not self.directed:
                self.adj[b].add(a)
        self.start = _label(initial["start"])
        if self.start not in self.adj:
            raise OpError(f"start node {self.start} is not in the graph")
        if len(self.adj) > MAX_ITEMS + 1:
            raise OpError(f"keep the graph to at most {MAX_ITEMS + 1} nodes")
        self.current: str | None = None
        self.queue: list[str] = [self.start]
        self.visited: list[str] = []

    def neighbours(self, n: str) -> list[str]:
        return sorted(self.adj[n], key=natural_key)

    def op_bfs_step(self):
        if not self.queue:
            raise OpError("BFS is finished: the queue is empty")
        self.current = self.queue.pop(0)
        self.visited.append(self.current)
        added = [m for m in self.neighbours(self.current) if m not in self.visited and m not in self.queue]
        self.queue += added
        return [self.current] + added

    def bfs_order(self) -> list[str]:
        order, queue = [], [self.start]
        while queue:
            n = queue.pop(0)
            order.append(n)
            queue += [m for m in self.neighbours(n) if m not in order and m not in queue]
        return order

    def state(self):
        return {"current": self.current, "queue": list(self.queue), "visited": list(self.visited)}

    def matches(self, claimed) -> bool:
        if not isinstance(claimed, dict):
            return False
        return normalize({k: claimed.get(k) for k in ("current", "queue", "visited")}) == normalize(self.state())

    def values(self) -> set[str]:
        return {normalize(n) for n in self.adj}

    def facts(self) -> dict:
        return {**self.state(), "bfs_order": self.bfs_order(), "size": len(self.adj)}

    def snapshot(self) -> dict:
        nodes = sorted(self.adj, key=natural_key)
        if self.directed:
            edges = [[a, b] for a in nodes for b in self.neighbours(a)]
        else:
            edges = [[a, b] for a in nodes for b in self.neighbours(a) if natural_key(a) < natural_key(b)]
        return {
            "nodes": nodes,
            "edges": edges,
            "directed": self.directed,
            "start": self.start,
            **self.state(),
        }


STRUCTURES = {cls.NAME: cls for cls in (Stack, Queue, LinkedList, BST, Graph)}
DISPLAY_NAMES = {
    "stack": "Stack",
    "queue": "Queue",
    "linked_list": "Linked list",
    "bst": "Binary search tree",
    "graph": "Breadth-first search",
}


def build(name: str, initial) -> Structure:
    if name not in STRUCTURES:
        raise OpError(f"unknown structure '{name}'; use one of: {', '.join(STRUCTURES)}")
    return STRUCTURES[name](initial)


def catalog() -> str:
    """The structure reference given to the language model."""
    return "\n".join("- " + cls.HELP for cls in STRUCTURES.values())
