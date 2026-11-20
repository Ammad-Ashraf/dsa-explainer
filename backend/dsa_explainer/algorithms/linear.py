"""Linear structures: stack, queue, deque and singly linked list."""

from __future__ import annotations

from .base import MAX_ITEMS, OpError, Structure, as_value


class _Linear(Structure):
    """A row of (id, value) items. Index 0 is the bottom / front / head."""

    CATEGORY = "linear"

    def __init__(self, initial) -> None:
        super().__init__()
        if not isinstance(initial, list):
            raise OpError(f"initial data for a {self.TITLE.lower()} must be a list of values")
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
            raise OpError(f"cannot {op}: the {self.TITLE.lower()} is empty")

    def state(self):
        return [v for _, v in self.items]

    def snapshot(self) -> dict:
        return {"items": [list(item) for item in self.items]}


class Stack(_Linear):
    NAME, TITLE, VIEW = "stack", "Stack", "stack"
    SUMMARY = "Last in, first out: push and pop at the top, like a pile of plates."
    DESCRIPTION = ("A stack keeps items in the order they arrived and only ever touches the top. Push puts an item "
                   "on top, pop takes the top item off, and peek reads it without removing it. Undo buttons, the "
                   "browser's back button and function calls all work this way.")
    COMPLEXITY = {"best": "O(1)", "average": "O(1)", "worst": "O(1)", "space": "O(n)"}
    PSEUDOCODE = ("push(x): top = top + 1; a[top] = x", "pop(): x = a[top]; top = top - 1; return x",
                  "peek(): return a[top]")
    KEYWORDS = ("stack", "lifo", "push", "pop", "undo", "plates")
    PRESETS = {"empty": [], "a few plates": [4, 9], "nearly full": [2, 5, 8, 6, 1]}
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
    NAME, TITLE, VIEW = "queue", "Queue", "queue"
    SUMMARY = "First in, first out: join at the rear, leave from the front, like a ticket line."
    DESCRIPTION = ("A queue serves items in the order they arrived. Enqueue adds an item at the rear, dequeue "
                   "removes the item at the front, and peek reads the front. Printers, message brokers and "
                   "breadth-first search all rely on queues.")
    COMPLEXITY = {"best": "O(1)", "average": "O(1)", "worst": "O(1)", "space": "O(n)"}
    PSEUDOCODE = ("enqueue(x): a[rear] = x; rear = rear + 1", "dequeue(): x = a[front]; front = front + 1; return x",
                  "peek(): return a[front]")
    KEYWORDS = ("queue", "fifo", "enqueue", "dequeue", "line", "print job", "ticket")
    PRESETS = {"empty": [], "print jobs": [3, 8], "busy line": [5, 2, 7, 4]}
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


class Deque(_Linear):
    NAME, TITLE, VIEW = "deque", "Deque", "queue"
    DIFFICULTY = "intermediate"
    SUMMARY = "A double-ended queue: add and remove at both the front and the rear."
    DESCRIPTION = ("A deque (double-ended queue) lets you push and pop at either end in constant time. It can act "
                   "as a stack, a queue or both at once, which is why sliding-window algorithms and undo/redo "
                   "histories use it.")
    COMPLEXITY = {"best": "O(1)", "average": "O(1)", "worst": "O(1)", "space": "O(n)"}
    PSEUDOCODE = ("push_front(x): front = front - 1; a[front] = x", "push_back(x): a[rear] = x; rear = rear + 1",
                  "pop_front(): x = a[front]; front = front + 1", "pop_back(): rear = rear - 1; x = a[rear]")
    KEYWORDS = ("deque", "double-ended", "double ended", "both ends", "sliding window")
    PRESETS = {"empty": [], "two items": [4, 6], "four items": [3, 9, 2, 7]}
    OPS = {"push_front": ("value",), "push_back": ("value",), "pop_front": (), "pop_back": (),
           "peek_front": (), "peek_back": ()}
    FACTS = ("front", "rear", "size", "items")
    HELP = (
        "deque (double-ended queue): initial = list of values from front to rear, e.g. [4, 6]. "
        "ops: push_front(value), push_back(value), pop_front(), pop_back(), peek_front(), peek_back(). "
        "state = list from front to rear. facts: front, rear (also called back), size, items (front to rear)."
    )

    def op_push_front(self, value):
        return [self._add(0, value)]

    def op_push_back(self, value):
        return [self._add(len(self.items), value)]

    def op_pop_front(self):
        self._need_items("pop_front")
        return [self.items.pop(0)[0]]

    def op_pop_back(self):
        self._need_items("pop_back")
        return [self.items.pop()[0]]

    def op_peek_front(self):
        self._need_items("peek_front")
        return [self.items[0][0]]

    def op_peek_back(self):
        self._need_items("peek_back")
        return [self.items[-1][0]]

    def facts(self) -> dict:
        first = self.items[0][1] if self.items else None
        last = self.items[-1][1] if self.items else None
        return {"front": first, "rear": last, "size": len(self.items), "items": self.state()}


class LinkedList(_Linear):
    NAME, TITLE, VIEW = "linked_list", "Linked list", "linked_list"
    SUMMARY = "Nodes that point to the next node: insert anywhere without shifting the rest."
    DESCRIPTION = ("A singly linked list stores each value in a node that points to the next one. Inserting or "
                   "deleting only re-links a pointer, but reaching a position means walking from the head, one "
                   "node at a time.")
    COMPLEXITY = {"best": "O(1)", "average": "O(n)", "worst": "O(n)", "space": "O(n)"}
    PSEUDOCODE = ("insert_head(x): n = Node(x); n.next = head; head = n",
                  "insert_at(i, x): walk i - 1 nodes from head; n.next = cur.next; cur.next = n",
                  "delete(x): walk until cur.next.value == x; cur.next = cur.next.next",
                  "search(x): walk from head until value == x")
    KEYWORDS = ("linked list", "linked-list", "node", "pointer", "next pointer", "singly")
    PRESETS = {"short list": [3, 8, 12], "one node": [5], "five nodes": [2, 4, 6, 8, 10]}
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
