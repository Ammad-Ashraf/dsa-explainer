"""Trees and heaps: binary search tree, tree traversals, min-heap and heap sort."""

from __future__ import annotations

from .base import MAX_ITEMS, OpError, Structure, as_int, normalize


class _Node:
    def __init__(self, nid: int, value: int) -> None:
        self.id, self.value = nid, value
        self.left: _Node | None = None
        self.right: _Node | None = None


def _norm_tree(t):
    if not isinstance(t, dict):
        return None if t in (None, [], {}) else normalize(t)
    return {"value": normalize(t.get("value")), "left": _norm_tree(t.get("left")), "right": _norm_tree(t.get("right"))}


class _Tree(Structure):
    CATEGORY = "trees"
    NOUN = "nodes"
    VIEW = "tree"

    def __init__(self) -> None:
        super().__init__()
        self.root: _Node | None = None

    @staticmethod
    def _number(v) -> int:
        return as_int(v, "a tree value", -99, 999)

    def _find(self, value: int):
        """The nodes compared while looking for value, its parent, and the node (or None)."""
        path, parent, node = [], None, self.root
        while node is not None and node.value != value:
            path.append(node)
            parent, node = node, (node.left if value < node.value else node.right)
        if node is not None:
            path.append(node)
        return path, parent, node

    def _insert(self, value):
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

    def _nodes(self, order: str) -> list[_Node]:
        def pre(n):
            return [n] + pre(n.left) + pre(n.right) if n else []

        def ino(n):
            return ino(n.left) + [n] + ino(n.right) if n else []

        def post(n):
            return post(n.left) + post(n.right) + [n] if n else []

        if order == "levelorder":
            out, level = [], [self.root] if self.root else []
            while level:
                out += level
                level = [c for n in level for c in (n.left, n.right) if c is not None]
            return out
        return {"preorder": pre, "inorder": ino, "postorder": post}[order](self.root)

    def _inorder(self, n):
        return self._inorder(n.left) + [n.value] + self._inorder(n.right) if n else []

    def _tree(self, n):
        return None if n is None else {"value": n.value, "left": self._tree(n.left), "right": self._tree(n.right)}

    def _tree_snapshot(self) -> dict:
        nodes = {}

        def add(n):
            if n is not None:
                nodes[n.id] = [n.value, n.left.id if n.left else None, n.right.id if n.right else None]
                add(n.left)
                add(n.right)

        add(self.root)
        return {"root": self.root.id if self.root else None, "nodes": nodes}

    def _shape_facts(self) -> dict:
        ino = self._inorder(self.root)
        return {
            "root": self.root.value if self.root else None, "size": len(ino),
            "min": ino[0] if ino else None, "max": ino[-1] if ino else None, "inorder": ino,
            "preorder": [n.value for n in self._nodes("preorder")],
            "postorder": [n.value for n in self._nodes("postorder")],
            "levelorder": [n.value for n in self._nodes("levelorder")],
        }


class BST(_Tree):
    NAME, TITLE = "bst", "Binary search tree"
    DIFFICULTY = "intermediate"
    SUMMARY = "Smaller values to the left, larger to the right: search by halving the tree."
    DESCRIPTION = ("In a binary search tree every node's left subtree holds smaller values and its right subtree "
                   "larger ones. Searching, inserting and deleting walk one path from the root, so a balanced tree "
                   "answers in about log n comparisons.")
    COMPLEXITY = {"best": "O(log n)", "average": "O(log n)", "worst": "O(n)", "space": "O(n)"}
    PSEUDOCODE = ("insert(x): walk left if x < node, right if x > node; attach x at the empty spot",
                  "search(x): walk left or right until the value equals x or the path ends",
                  "delete(x): a leaf goes; one child moves up; two children: copy the in-order successor")
    KEYWORDS = ("bst", "binary search tree", "search tree", "successor")
    PRESETS = {"balanced": [8, 3, 10, 1, 6, 14], "small": [5, 2, 7], "a chain": [1, 2, 3, 4]}
    OPS = {"insert": ("value",), "search": ("value",), "delete": ("value",)}
    FACTS = ("root", "size", "min", "max", "inorder", "preorder", "postorder", "levelorder", "comparisons")
    STRIP = ("root", "size", "min", "max", "comparisons")
    OP_LINES = {"insert": (0,), "search": (1,), "delete": (2,)}
    HELP = (
        "bst (binary search tree, no duplicates): initial = list of whole numbers inserted in that order, "
        "e.g. [8, 3, 10]. ops: insert(value), search(value), delete(value); a node with two children is "
        "replaced by its in-order successor (the smallest value in its right subtree). "
        'state = nested object {"value": 8, "left": {...} or null, "right": {...} or null}, null if empty. '
        "facts: root, size, min, max, inorder, preorder, postorder, levelorder, comparisons (values the last "
        "operation compared on its way down from the root)."
    )

    def __init__(self, initial) -> None:
        super().__init__()
        if not isinstance(initial, list):
            raise OpError("initial data for a bst must be a list of whole numbers")
        for v in initial:
            self.op_insert(v)
        self.comparisons: int | None = None

    def op_insert(self, value):
        focus = self._insert(value)
        self.comparisons = len(focus) - 1  # every node on the way down; the new node is not compared
        return focus

    def op_search(self, value):
        path, _, _ = self._find(self._number(value))
        self.comparisons = len(path)
        return [n.id for n in path]

    def op_delete(self, value):
        value = self._number(value)
        path, parent, node = self._find(value)
        self.comparisons = len(path)
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

    def state(self):
        return self._tree(self.root)

    def matches(self, claimed) -> bool:
        return _norm_tree(claimed) == _norm_tree(self.state())

    def facts(self) -> dict:
        return {**self._shape_facts(), "comparisons": self.comparisons}

    def snapshot(self) -> dict:
        return self._tree_snapshot()


ORDERS = ("preorder", "inorder", "postorder", "levelorder")


class TreeTraversal(_Tree):
    NAME, TITLE = "tree_traversal", "Tree traversals"
    SUMMARY = "Visit every node in pre-order, in-order, post-order or level order."
    DESCRIPTION = ("A traversal visits every node of a tree exactly once. Pre-order visits a node before its "
                   "children, in-order between them (which lists a BST in sorted order), post-order after them, "
                   "and level order goes row by row from the root.")
    COMPLEXITY = {"best": "O(n)", "average": "O(n)", "worst": "O(n)", "space": "O(h)"}
    PSEUDOCODE = ("preorder(n): visit(n); preorder(n.left); preorder(n.right)",
                  "inorder(n): inorder(n.left); visit(n); inorder(n.right)",
                  "postorder(n): postorder(n.left); postorder(n.right); visit(n)",
                  "levelorder: queue = [root]; repeat: n = dequeue; visit(n); enqueue its children")
    KEYWORDS = ("traversal", "traverse", "inorder", "in-order", "preorder", "pre-order", "postorder", "post-order",
                "level order", "level-order")
    PRESETS = {"in-order": {"values": [8, 3, 10, 1, 6, 14], "order": "inorder"},
               "pre-order": {"values": [8, 3, 10, 1, 6], "order": "preorder"},
               "level order": {"values": [5, 3, 8, 2, 4, 9], "order": "levelorder"}}
    OPS = {"visit": ()}
    FACTS = ("current", "visited", "order", "root", "size")
    STRIP = ("current", "root", "size")
    OP_LINES = {"visit": (0, 1, 2, 3)}  # every order's line; code_lines() picks the lesson's order
    HELP = (
        'tree_traversal: initial = {"values": [8, 3, 10, 1, 6], "order": "inorder"}: the values are inserted '
        "into a binary search tree in that order; order is preorder, inorder, postorder or levelorder. "
        "ops: visit() visits the next node in that order. "
        'state = {"current": the value just visited, "visited": [values in visiting order]}. '
        "facts: current, visited, order (the full traversal), root, size."
    )

    def __init__(self, initial) -> None:
        super().__init__()
        if not isinstance(initial, dict) or not isinstance(initial.get("values"), list):
            raise OpError('initial data must be {"values": [whole numbers], "order": "inorder"}')
        self.order = str(initial.get("order", "inorder")).replace("-", "").replace(" ", "").lower()
        if self.order not in ORDERS:
            raise OpError(f"order must be one of: {', '.join(ORDERS)}")
        for v in initial["values"]:
            self._insert(v)
        if self.root is None:
            raise OpError("the tree needs at least one value")
        self.sequence = self._nodes(self.order)
        self.visited: list[_Node] = []

    def op_visit(self):
        if len(self.visited) == len(self.sequence):
            raise OpError("the traversal is finished: every node was visited")
        node = self.sequence[len(self.visited)]
        self.visited.append(node)
        return [node.id]

    def code_lines(self, op):
        return [ORDERS.index(self.order)]

    def state(self):
        return {"current": self.visited[-1].value if self.visited else None,
                "visited": [n.value for n in self.visited]}

    def matches(self, claimed) -> bool:
        return isinstance(claimed, dict) and normalize(
            {k: claimed.get(k) for k in ("current", "visited")}) == normalize(self.state())

    def values(self) -> set[str]:
        return {normalize(v) for v in self._inorder(self.root)}

    def facts(self) -> dict:
        shape = self._shape_facts()
        return {**self.state(), "order": [n.value for n in self.sequence], "root": shape["root"],
                "size": shape["size"]}

    def snapshot(self) -> dict:
        return {**self._tree_snapshot(), "visited": [n.id for n in self.visited],
                "current": self.visited[-1].id if self.visited else None,
                "label": {"preorder": "pre-order", "inorder": "in-order", "postorder": "post-order",
                          "levelorder": "level order"}[self.order]}


class _ArrayHeap(Structure):
    """A binary heap stored in an array: children of i are 2i + 1 and 2i + 2."""

    CATEGORY = "trees"
    VIEW = "heap"
    NOUN = "values"

    def __init__(self) -> None:
        super().__init__()
        self.items: list[tuple[int, int]] = []
        self.swaps: int | None = None  # swaps made by the last operation

    def run(self, op: str, args: dict | None = None) -> list:
        self.swaps = 0
        return super().run(op, args)

    def _before(self, a: int, b: int) -> bool:
        raise NotImplementedError

    def _swap(self, i: int, j: int) -> None:
        self.items[i], self.items[j] = self.items[j], self.items[i]
        self.swaps = (self.swaps or 0) + 1

    def _sift_up(self, i: int) -> list[int]:
        path = [self.items[i][0]]
        while i > 0 and self._before(self.items[i][1], self.items[(i - 1) // 2][1]):
            parent = (i - 1) // 2
            self._swap(i, parent)
            path.append(self.items[i][0])
            i = parent
        return path

    def _sift_down(self, i: int, size: int) -> list[int]:
        path = []
        while True:
            best, left, right = i, 2 * i + 1, 2 * i + 2
            if left < size and self._before(self.items[left][1], self.items[best][1]):
                best = left
            if right < size and self._before(self.items[right][1], self.items[best][1]):
                best = right
            if best == i:
                return path
            path.append(self.items[best][0])
            self._swap(i, best)
            i = best

    def _value(self, v) -> int:
        return as_int(v, "a heap value", -99, 999)


class MinHeap(_ArrayHeap):
    NAME, TITLE = "min_heap", "Min-heap (priority queue)"
    DIFFICULTY = "intermediate"
    SUMMARY = "The smallest value always sits at the root: a priority queue in an array."
    DESCRIPTION = ("A min-heap is a complete binary tree where every parent is smaller than its children, stored "
                   "level by level in an array. Insert adds at the end and sifts up; extract-min moves the last "
                   "value to the root and sifts down. Both take about log n swaps.")
    COMPLEXITY = {"best": "O(1)", "average": "O(log n)", "worst": "O(log n)", "space": "O(n)"}
    PSEUDOCODE = ("insert(x): a.append(x); while x < parent: swap with parent",
                  "extract_min(): m = a[0]; a[0] = a.pop(); while a child is smaller: swap with the smaller child",
                  "peek(): return a[0]")
    KEYWORDS = ("heap", "min-heap", "min heap", "priority queue", "sift", "heapify", "extract min", "extract-min")
    PRESETS = {"empty": [], "small heap": [3, 8, 5], "six values": [9, 4, 7, 1, 8, 2]}
    OPS = {"insert": ("value",), "extract_min": (), "peek": ()}
    FACTS = ("root", "min", "size", "items", "swaps")
    STRIP = ("root", "size", "swaps")
    OP_LINES = {"insert": (0,), "extract_min": (1,), "peek": (2,)}
    HELP = (
        "min_heap (binary min-heap stored as an array, children of index i at 2i+1 and 2i+2): initial = list of "
        "whole numbers inserted in that order, e.g. [9, 4, 7]. ops: insert(value) appends then swaps with its "
        "parent while smaller; extract_min() removes the root, moves the last value to the root, then swaps it "
        "with its smaller child while larger; peek() reads the root. state = the array, e.g. [4, 9, 7]. "
        "facts: root (= min), min, size, items (the array), swaps (made by the last operation)."
    )

    def __init__(self, initial) -> None:
        super().__init__()
        if not isinstance(initial, list):
            raise OpError("initial data for a min-heap must be a list of whole numbers")
        for v in initial:
            self.op_insert(v)
        self.swaps = None

    def _before(self, a, b):
        return a < b

    def op_insert(self, value):
        if len(self.items) >= MAX_ITEMS:
            raise OpError(f"keep at most {MAX_ITEMS} values so the picture stays readable")
        self.items.append((self.new_id(), self._value(value)))
        return self._sift_up(len(self.items) - 1)

    def op_extract_min(self):
        if not self.items:
            raise OpError("cannot extract_min: the heap is empty")
        root = self.items[0][0]
        last = self.items.pop()
        if self.items:
            self.items[0] = last
            return [root, last[0]] + self._sift_down(0, len(self.items))
        return [root]

    def op_peek(self):
        if not self.items:
            raise OpError("cannot peek: the heap is empty")
        return [self.items[0][0]]

    def state(self):
        return [v for _, v in self.items]

    def facts(self) -> dict:
        root = self.items[0][1] if self.items else None
        return {"root": root, "min": root, "size": len(self.items), "items": self.state(), "swaps": self.swaps}

    def snapshot(self) -> dict:
        return {"items": [list(i) for i in self.items], "heap_size": len(self.items), "kind": "min"}


class HeapSort(_ArrayHeap):
    NAME, TITLE = "heap_sort", "Heap sort"
    CATEGORY = "sorting"
    DIFFICULTY = "advanced"
    SUMMARY = "Build a max-heap, then move the root to the end, again and again."
    DESCRIPTION = ("Heap sort first rearranges the array into a max-heap, so the largest value is at the front. "
                   "It then swaps that root with the last unsorted value, shrinks the heap by one and sifts the new "
                   "root down. The sorted part grows from the back, in place and in n log n time.")
    COMPLEXITY = {"best": "O(n log n)", "average": "O(n log n)", "worst": "O(n log n)", "space": "O(1)"}
    PSEUDOCODE = ("build_heap(): for i from n/2 - 1 down to 0: sift_down(i)",
                  "extract_max(): swap a[0] with a[end]; end = end - 1; sift_down(0) within the heap")
    KEYWORDS = ("heap sort", "heapsort", "max-heap", "max heap")
    PRESETS = {"six values": [4, 10, 3, 5, 1, 8], "reversed": [6, 5, 4, 3, 2], "five values": [7, 2, 9, 4, 6]}
    OPS = {"build_heap": (), "extract_max": ()}
    FACTS = ("root", "heap_size", "sorted", "size", "items", "swaps")
    STRIP = ("root", "heap_size", "swaps", "sorted")
    FACT_LABELS = {"heap_size": "heap size"}
    OP_LINES = {"build_heap": (0,), "extract_max": (1,)}
    HELP = (
        "heap_sort (in place, max-heap, children of index i at 2i+1 and 2i+2): initial = list of whole numbers. "
        "ops: build_heap() turns the array into a max-heap (sift down from index n/2 - 1 to 0), and must come "
        "first; extract_max() swaps the root with the last value of the heap, shrinks the heap by one and sifts "
        "the new root down. "
        'state = {"array": [...], "heap_size": number of values still in the heap}. '
        "facts: root (largest value in the heap), heap_size, sorted (the sorted values at the end), size, "
        "items (the whole array), swaps (made by the last operation, the root swap included)."
    )

    def __init__(self, initial) -> None:
        super().__init__()
        if not isinstance(initial, list) or not initial:
            raise OpError("initial data for heap sort must be a non-empty list of whole numbers")
        if len(initial) > MAX_ITEMS:
            raise OpError(f"keep at most {MAX_ITEMS} values so the picture stays readable")
        self.items = [(self.new_id(), self._value(v)) for v in initial]
        self.heap_size = len(self.items)
        self.built = False

    def _before(self, a, b):
        return a > b

    def op_build_heap(self):
        if self.built:
            raise OpError("the heap is already built")
        path = []
        for i in range(len(self.items) // 2 - 1, -1, -1):
            path += self._sift_down(i, self.heap_size)
        self.built = True
        return path or [self.items[0][0]]

    def op_extract_max(self):
        if not self.built:
            raise OpError("call build_heap() first")
        if self.heap_size <= 1:
            raise OpError("the array is already sorted")
        end = self.heap_size - 1
        moved = [self.items[0][0], self.items[end][0]]
        self._swap(0, end)
        self.heap_size = end
        return moved + self._sift_down(0, self.heap_size)

    def state(self):
        return {"array": [v for _, v in self.items], "heap_size": self.heap_size}

    def values(self) -> set[str]:
        return {normalize(v) for _, v in self.items}

    def facts(self) -> dict:
        return {"root": self.items[0][1] if self.heap_size else None, "heap_size": self.heap_size,
                "sorted": [v for _, v in self.items[self.heap_size:]] if self.heap_size < len(self.items) else [],
                "size": len(self.items), "items": [v for _, v in self.items], "swaps": self.swaps}

    def snapshot(self) -> dict:
        return {"items": [list(i) for i in self.items], "heap_size": self.heap_size, "kind": "max",
                "built": self.built}
