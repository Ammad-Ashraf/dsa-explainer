"""Arrays: sorting (bubble, insertion, selection, merge, quick) and searching (linear, binary).

Each operation is one meaningful chunk of the algorithm (a whole bubble pass,
one insertion, one merge, one partition, one probe), so a lesson shows the
algorithm in 4 to 8 steps. Snapshots carry the array plus what the picture
needs: the sorted region, named pointers and the active range.
"""

from __future__ import annotations

from .base import MAX_ITEMS, OpError, Structure, as_int, normalize

MAX_ARRAY = MAX_ITEMS + 1


class _Array(Structure):
    VIEW = "array"
    NOUN = "values"

    def __init__(self, values) -> None:
        super().__init__()
        if not isinstance(values, list) or not values:
            raise OpError(f"initial data for {self.TITLE.lower()} must be a non-empty list of whole numbers")
        if len(values) > MAX_ARRAY:
            raise OpError(f"keep at most {MAX_ARRAY} values so the picture stays readable")
        self.items = [(self.new_id(), as_int(v, "an array value", -99, 999)) for v in values]

    @property
    def a(self) -> list[int]:
        return [v for _, v in self.items]

    def _swap(self, i: int, j: int) -> None:
        self.items[i], self.items[j] = self.items[j], self.items[i]

    def snapshot(self) -> dict:
        return {"items": [list(i) for i in self.items], "sorted": [], "pointers": {}, "range": None, "faded": [],
                "style": "bars" if self.CATEGORY == "sorting" else "cells"}


# --- sorting -------------------------------------------------------------------------


class _Sort(_Array):
    CATEGORY = "sorting"
    FACT_LABELS = {"sorted_count": "in place", "pivot_index": "pivot index"}
    PRESETS = {"six values": [5, 1, 4, 2, 8, 3], "reversed": [6, 5, 4, 3, 2, 1], "nearly sorted": [1, 2, 4, 3, 5]}

    def __init__(self, initial) -> None:
        super().__init__(initial)
        self.last: dict = {}

    def state(self):
        return self.a

    def _sorted_indices(self) -> list[int]:
        raise NotImplementedError

    def facts(self) -> dict:
        return {"items": self.a, "size": len(self.items), "sorted_count": len(self._sorted_indices()), **self.last}

    def snapshot(self) -> dict:
        return {**super().snapshot(), "sorted": self._sorted_indices()}


class BubbleSort(_Sort):
    NAME, TITLE = "bubble_sort", "Bubble sort"
    SUMMARY = "Swap neighbours that are out of order; the largest value bubbles to the end each pass."
    DESCRIPTION = ("Bubble sort walks the array comparing each pair of neighbours and swapping them when they are "
                   "in the wrong order. After each pass the largest remaining value has bubbled to its final place "
                   "at the end. If a pass makes no swaps, the array is sorted and it can stop early.")
    COMPLEXITY = {"best": "O(n)", "average": "O(n^2)", "worst": "O(n^2)", "space": "O(1)"}
    PSEUDOCODE = ("for each pass:", "    for j from 0 to the end of the unsorted part - 2:",
                  "        if a[j] > a[j + 1]: swap them", "    stop early if the pass made no swaps")
    KEYWORDS = ("bubble sort", "bubble", "bubblesort")
    OPS = {"bubble_pass": ()}
    FACTS = ("items", "size", "sorted_count", "swaps", "comparisons", "placed")
    STRIP = ("comparisons", "swaps", "placed", "sorted_count")
    OP_LINES = {"bubble_pass": (1, 2, 3)}  # line 3 (stop early) only when the pass made no swaps
    HELP = (
        "bubble_sort: initial = list of whole numbers, e.g. [5, 1, 4, 2]. ops: bubble_pass() makes one full pass "
        "over the unsorted part, comparing neighbours from the left and swapping when the left one is larger; "
        "the largest unsorted value ends in its final place. If a pass makes no swaps the whole array is sorted. "
        "state = the array. facts: items, size, sorted_count (values in their final place), swaps and "
        "comparisons (in the last pass), placed (the value the last pass put in place)."
    )

    def __init__(self, initial) -> None:
        super().__init__(initial)
        self.fixed = 0

    def _sorted_indices(self):
        return list(range(len(self.items) - self.fixed, len(self.items)))

    def op_bubble_pass(self):
        n = len(self.items)
        if self.fixed >= n:
            raise OpError("the array is already sorted")
        end, swaps, focus = n - self.fixed, 0, []
        for j in range(end - 1):
            if self.items[j][1] > self.items[j + 1][1]:
                self._swap(j, j + 1)
                swaps += 1
                focus.append(self.items[j + 1][0])
        placed = self.items[end - 1][1]
        self.fixed = n if swaps == 0 or self.fixed + 1 >= n - 1 else self.fixed + 1
        self.last = {"swaps": swaps, "comparisons": end - 1, "placed": placed}
        return focus or [self.items[end - 1][0]]

    def code_lines(self, op):
        return [1, 2, 3] if self.last.get("swaps") == 0 else [1, 2]


class InsertionSort(_Sort):
    NAME, TITLE = "insertion_sort", "Insertion sort"
    SUMMARY = "Take the next value and slide it left into place, like sorting playing cards."
    DESCRIPTION = ("Insertion sort keeps a sorted part at the front. Each step takes the next value, shifts every "
                   "larger sorted value one place right, and drops the value into the gap. It is fast on small or "
                   "nearly sorted arrays.")
    COMPLEXITY = {"best": "O(n)", "average": "O(n^2)", "worst": "O(n^2)", "space": "O(1)"}
    PSEUDOCODE = ("for i from 1 to n - 1:", "    key = a[i]; j = i - 1",
                  "    while j >= 0 and a[j] > key: a[j + 1] = a[j]; j = j - 1", "    a[j + 1] = key")
    KEYWORDS = ("insertion sort", "insertion", "playing cards", "cards")
    OPS = {"insert_next": ()}
    FACTS = ("items", "size", "sorted_count", "key", "shifts", "comparisons")
    STRIP = ("key", "comparisons", "shifts", "sorted_count")
    OP_LINES = {"insert_next": (1, 2, 3)}
    HELP = (
        "insertion_sort: initial = list of whole numbers. The first value alone counts as sorted. ops: "
        "insert_next() takes the first value after the sorted part (the key), shifts every larger sorted value "
        "one place right, and puts the key in the gap. state = the array. facts: items, size, sorted_count "
        "(length of the sorted part), key (the value just inserted), shifts (values shifted in the last step), "
        "comparisons (values compared with the key in the last step)."
    )

    def __init__(self, initial) -> None:
        super().__init__(initial)
        self.k = 1

    def _sorted_indices(self):
        return list(range(min(self.k, len(self.items))))

    def op_insert_next(self):
        if self.k >= len(self.items):
            raise OpError("the array is already sorted")
        item = self.items.pop(self.k)
        j = self.k
        while j > 0 and self.items[j - 1][1] > item[1]:
            j -= 1
        shifted = [iid for iid, _ in self.items[j:self.k]]
        self.items.insert(j, item)
        # every shifted value was compared, plus the smaller value that stopped the walk (if any)
        self.last = {"key": item[1], "shifts": self.k - j, "comparisons": self.k - j + (1 if j > 0 else 0)}
        self.k += 1
        return [item[0]] + shifted


class SelectionSort(_Sort):
    NAME, TITLE = "selection_sort", "Selection sort"
    SUMMARY = "Find the smallest unsorted value and swap it to the front of the unsorted part."
    DESCRIPTION = ("Selection sort grows a sorted part at the front. Each step scans the unsorted part for its "
                   "smallest value and swaps it into the next position. It always makes about n squared over two "
                   "comparisons but at most n - 1 swaps.")
    COMPLEXITY = {"best": "O(n^2)", "average": "O(n^2)", "worst": "O(n^2)", "space": "O(1)"}
    PSEUDOCODE = ("for i from 0 to n - 2:", "    m = index of the smallest value in a[i..n - 1]",
                  "    swap a[i] and a[m]")
    KEYWORDS = ("selection sort", "selection", "select the minimum")
    OPS = {"select_next": ()}
    FACTS = ("items", "size", "sorted_count", "selected", "swapped", "comparisons")
    STRIP = ("selected", "comparisons", "swapped", "sorted_count")
    OP_LINES = {"select_next": (1, 2)}
    HELP = (
        "selection_sort: initial = list of whole numbers. ops: select_next() finds the smallest value in the "
        "unsorted part (the first one if there are ties) and swaps it with the first unsorted value; when one "
        "unsorted value is left it is already in place. state = the array. facts: items, size, sorted_count, "
        "selected (the smallest value just moved), swapped (yes or no: no when it was already in place), "
        "comparisons (made while scanning in the last step)."
    )

    def __init__(self, initial) -> None:
        super().__init__(initial)
        self.k = 0 if len(self.items) > 1 else 1  # one value is already sorted

    def _sorted_indices(self):
        return list(range(self.k))

    def op_select_next(self):
        n = len(self.items)
        if self.k >= n - 1:
            raise OpError("the array is already sorted")
        m = min(range(self.k, n), key=lambda i: (self.items[i][1], i))
        swapped = m != self.k
        focus = [self.items[m][0]] + ([self.items[self.k][0]] if swapped else [])
        self._swap(self.k, m)
        self.last = {"selected": self.items[self.k][1], "swapped": swapped, "comparisons": n - self.k - 1}
        self.k += 1
        if self.k == n - 1:
            self.k = n
        return focus


class MergeSort(_Sort):
    NAME, TITLE = "merge_sort", "Merge sort"
    DIFFICULTY = "intermediate"
    SUMMARY = "Merge sorted runs of 1, then 2, then 4: divide and conquer, bottom up."
    DESCRIPTION = ("Merge sort treats every value as a sorted run of length one, then repeatedly merges "
                   "neighbouring runs into longer sorted runs: pairs, then fours, then eights. Merging two sorted "
                   "runs only needs one pass, so the whole sort takes n log n time, whatever the input.")
    COMPLEXITY = {"best": "O(n log n)", "average": "O(n log n)", "worst": "O(n log n)", "space": "O(n)"}
    PSEUDOCODE = ("width = 1", "while width < n:", "    for each pair of neighbouring runs of this width: merge them",
                  "    width = width * 2")
    KEYWORDS = ("merge sort", "mergesort", "merging", "divide and conquer")
    OPS = {"merge_next": ()}
    FACTS = ("items", "size", "width", "merged", "low", "high")
    STRIP = ("width", "low", "high", "merged")
    FACT_LABELS = {"width": "run width"}
    OP_LINES = {"merge_next": (2,)}
    HELP = (
        "merge_sort (bottom-up): initial = list of whole numbers. Runs start with width 1. ops: merge_next() "
        "merges the next pair of neighbouring runs of the current width, left to right; a run with no partner "
        "waits; after the last pair of a width, the width doubles. state = the array. facts: items, size, width "
        "(the run width of the last merge), merged (the merged values), low and high (first and last index of "
        "the merged part)."
    )

    def __init__(self, initial) -> None:
        super().__init__(initial)
        self.width, self.start = 1, 0

    def _sorted_indices(self):
        return list(range(len(self.items))) if self.width >= len(self.items) else []

    def op_merge_next(self):
        n = len(self.items)
        while self.width < n:
            lo, mid, hi = self.start, min(self.start + self.width, n), min(self.start + 2 * self.width, n)
            self.start += 2 * self.width
            if self.start >= n:
                self.width, self.start = self.width * 2, 0
            if mid < hi:  # a run with no partner just waits for the next width
                part = sorted(self.items[lo:hi], key=lambda item: item[1])  # stable: equal values keep their order
                self.items[lo:hi] = part
                self.last = {"width": mid - lo, "merged": [v for _, v in part], "low": lo, "high": hi - 1}
                return [iid for iid, _ in part]
        raise OpError("the array is already sorted")

    def snapshot(self) -> dict:
        snap = super().snapshot()
        if self.last:
            snap["range"] = [self.last["low"], self.last["high"]]
        return snap


class QuickSort(_Sort):
    NAME, TITLE = "quick_sort", "Quick sort"
    DIFFICULTY = "advanced"
    SUMMARY = "Pick a pivot, put smaller values left and larger right, then sort each side."
    DESCRIPTION = ("Quick sort picks a pivot (here the last value of the range), moves every smaller value before "
                   "it and every other value after it, and so puts the pivot in its final place. It then sorts the "
                   "left and right parts the same way. It is usually the fastest sort in practice.")
    COMPLEXITY = {"best": "O(n log n)", "average": "O(n log n)", "worst": "O(n^2)", "space": "O(log n)"}
    PSEUDOCODE = ("partition(lo, hi): pivot = a[hi]; i = lo",
                  "    for j from lo to hi - 1: if a[j] < pivot: swap a[i], a[j]; i = i + 1",
                  "    swap a[i], a[hi]  (the pivot is now in place)", "quicksort the left part, then the right part")
    KEYWORDS = ("quick sort", "quicksort", "pivot", "partition", "lomuto")
    OPS = {"partition_next": ()}
    FACTS = ("items", "size", "sorted_count", "pivot", "pivot_index", "low", "high", "comparisons", "swaps")
    STRIP = ("pivot", "pivot_index", "comparisons", "swaps", "sorted_count")
    OP_LINES = {"partition_next": (0, 1, 2)}
    FACT_WORDS = {"pivot": "pivot"}
    HELP = (
        "quick_sort (Lomuto partition, pivot = last value of the range): initial = list of whole numbers. "
        "ops: partition_next() partitions the next pending range: values smaller than the pivot move to the "
        "front of the range in their order, then the pivot goes right after them, in its final place. The first "
        "range is the whole array; afterwards the left part is partitioned before the right part, and parts "
        "with fewer than two values are already sorted. state = the array. facts: items, size, sorted_count "
        "(values known to be in place), pivot (value), pivot_index, low and high (the range partitioned), "
        "comparisons (with the pivot) and swaps (that moved a value) in the last partition."
    )

    def __init__(self, initial) -> None:
        super().__init__(initial)
        n = len(self.items)
        self.pending = [(0, n - 1)] if n > 1 else []
        self.done: set[int] = set() if n > 1 else {0}

    def _sorted_indices(self):
        return sorted(self.done)

    def op_partition_next(self):
        if not self.pending:
            raise OpError("the array is already sorted")
        lo, hi = self.pending.pop()
        pivot = self.items[hi][1]
        i, moved, swaps = lo, [], 0
        for j in range(lo, hi):
            if self.items[j][1] < pivot:
                if i != j:
                    moved += [self.items[j][0], self.items[i][0]]
                    swaps += 1
                self._swap(i, j)
                i += 1
        swaps += i != hi
        self._swap(i, hi)
        self.done.add(i)
        for a, b in ((lo, i - 1), (i + 1, hi)):
            if b - a < 1 and 0 <= a <= b:
                self.done.add(a)
        if hi - (i + 1) >= 1:
            self.pending.append((i + 1, hi))
        if (i - 1) - lo >= 1:
            self.pending.append((lo, i - 1))
        if not self.pending:
            self.done = set(range(len(self.items)))
        self.last = {"pivot": pivot, "pivot_index": i, "low": lo, "high": hi, "comparisons": hi - lo,
                     "swaps": swaps}
        return moved + [self.items[i][0]]

    def snapshot(self) -> dict:
        snap = super().snapshot()
        if self.last:
            snap["range"] = [self.last["low"], self.last["high"]]
            snap["pointers"] = {"pivot": self.last["pivot_index"]}
        return snap


# --- searching -----------------------------------------------------------------------


class _Search(_Array):
    CATEGORY = "searching"

    def __init__(self, initial) -> None:
        if not isinstance(initial, dict) or not isinstance(initial.get("array"), list) or "target" not in initial:
            raise OpError('initial data must be {"array": [whole numbers], "target": a number}')
        super().__init__(initial["array"])
        self.target = as_int(initial["target"], "the target", -99, 999)
        self.found: int | None = None
        self.finished = False

    def values(self) -> set[str]:
        return {normalize(v) for v in self.a} | {normalize(self.target)}


class LinearSearch(_Search):
    NAME, TITLE = "linear_search", "Linear search"
    SUMMARY = "Check each value from the left until you find the target or run out."
    DESCRIPTION = ("Linear search looks at every value in turn, from the first, until it finds the target. It "
                   "works on any array, sorted or not, but may need to look at every value.")
    COMPLEXITY = {"best": "O(1)", "average": "O(n)", "worst": "O(n)", "space": "O(1)"}
    PSEUDOCODE = ("for i from 0 to n - 1:", "    if a[i] == target: return i", "return not found")
    KEYWORDS = ("linear search", "sequential search", "find a value", "linear")
    PRESETS = {"found in the middle": {"array": [7, 3, 9, 4, 6], "target": 9},
               "not in the array": {"array": [5, 2, 8, 1], "target": 6},
               "first place": {"array": [4, 8, 1, 5], "target": 4}}
    OPS = {"check_next": ()}
    FACTS = ("current", "index", "found", "target", "size", "items", "comparisons")
    STRIP = ("target", "index", "current", "comparisons", "found")
    OP_LINES = {"check_next": (1, 2)}  # code_lines() adds line 2 only when the search ends without finding it
    FACT_LABELS = {"current": "value"}
    HELP = (
        'linear_search: initial = {"array": [7, 3, 9, 4], "target": 9}. ops: check_next() compares the next '
        "value, from index 0, with the target; the search finishes when they are equal or the array ends. "
        'state = {"index": index just checked, "value": the value there, "found": true or false, '
        '"finished": true or false}. facts: current (the value just checked), index, found (yes or no), target, '
        "size, items, comparisons (values checked so far)."
    )

    def __init__(self, initial) -> None:
        super().__init__(initial)
        self.i = -1

    def op_check_next(self):
        if self.finished:
            raise OpError("the search is finished")
        self.i += 1
        if self.items[self.i][1] == self.target:
            self.found, self.finished = self.i, True
        elif self.i == len(self.items) - 1:
            self.finished = True
        return [self.items[self.i][0]]

    def state(self):
        checked = self.i >= 0
        return {"index": self.i if checked else None, "value": self.items[self.i][1] if checked else None,
                "found": self.found is not None, "finished": self.finished}

    def facts(self) -> dict:
        s = self.state()
        return {"current": s["value"], "index": s["index"], "found": s["found"], "target": self.target,
                "size": len(self.items), "items": self.a, "comparisons": self.i + 1}

    def code_lines(self, op):
        return [1, 2] if self.finished and self.found is None else [1]

    def snapshot(self) -> dict:
        snap = super().snapshot()
        snap["target"] = self.target
        if self.i >= 0:
            snap["pointers"] = {"i": self.i}
            snap["faded"] = [k for k in range(self.i) if k != self.found]
        if self.found is not None:
            snap["found"] = self.found
        return snap


class BinarySearch(_Search):
    NAME, TITLE = "binary_search", "Binary search"
    SUMMARY = "Halve a sorted array each step by checking the middle value."
    DESCRIPTION = ("Binary search needs a sorted array. It compares the target with the middle value of the "
                   "current range: equal means found; smaller means the target can only be on the left, larger "
                   "only on the right. Each check halves the range, so even a million values need about 20 checks.")
    COMPLEXITY = {"best": "O(1)", "average": "O(log n)", "worst": "O(log n)", "space": "O(1)"}
    PSEUDOCODE = ("low = 0; high = n - 1", "while low <= high:", "    mid = (low + high) / 2, rounded down",
                  "    if a[mid] == target: found", "    if a[mid] < target: low = mid + 1 else: high = mid - 1")
    KEYWORDS = ("binary search", "bisect", "halving", "sorted array", "divide the search")
    REQUIRES = "a sorted array"
    PRESETS = {"found": {"array": [1, 3, 5, 7, 9, 11, 13], "target": 9},
               "not found": {"array": [2, 4, 6, 8, 10, 12], "target": 5},
               "first value": {"array": [3, 6, 9, 12, 15], "target": 3}}
    OPS = {"probe": ()}
    FACTS = ("low", "high", "mid", "middle", "found", "target", "size", "items", "comparisons")
    STRIP = ("target", "low", "mid", "high", "comparisons", "found")
    OP_LINES = {"probe": (2, 3, 4)}  # code_lines() picks "found" or the half that is kept
    FACT_WORDS = {"middle": "middle"}
    HELP = (
        'binary_search: initial = {"array": [1, 3, 5, 7, 9], "target": 7}; the array must be sorted ascending. '
        "Before the first step low = 0 and high = n - 1. ops: probe() sets mid = (low + high) // 2 and compares "
        "the middle value with the target: equal finishes (found); a smaller middle value sets low = mid + 1; "
        "a larger one sets high = mid - 1; low > high finishes (not found). "
        'state = {"low": ..., "high": ..., "mid": index just checked, "found": true or false, "finished": true '
        'or false}. facts: low, high, mid (an index), middle (the value at mid), found (yes or no), target, '
        "size, items, comparisons (probes so far)."
    )

    def __init__(self, initial) -> None:
        super().__init__(initial)
        if self.a != sorted(self.a):
            raise OpError("binary search needs a sorted array (ascending)")
        self.low, self.high, self.mid = 0, len(self.items) - 1, None
        self.probes = 0

    def op_probe(self):
        if self.finished:
            raise OpError("the search is finished")
        self.mid = (self.low + self.high) // 2
        self.probes += 1
        value = self.items[self.mid][1]
        if value == self.target:
            self.found, self.finished = self.mid, True
        elif value < self.target:
            self.low = self.mid + 1
        else:
            self.high = self.mid - 1
        if self.low > self.high:
            self.finished = True
        return [self.items[self.mid][0]]

    def state(self):
        return {"low": self.low, "high": self.high, "mid": self.mid, "found": self.found is not None,
                "finished": self.finished}

    def facts(self) -> dict:
        return {**self.state(), "middle": self.items[self.mid][1] if self.mid is not None else None,
                "target": self.target, "size": len(self.items), "items": self.a, "comparisons": self.probes}

    def code_lines(self, op):
        return [2, 3] if self.found is not None else [2, 4]

    def snapshot(self) -> dict:
        snap = super().snapshot()
        snap["target"] = self.target
        pointers = {"low": self.low, "high": self.high} if self.low <= self.high else {}
        if self.mid is not None:
            pointers["mid"] = self.mid
        snap["pointers"] = pointers
        snap["range"] = [self.low, self.high] if self.low <= self.high else None
        snap["faded"] = [k for k in range(len(self.items)) if not self.low <= k <= self.high and k != self.found]
        if self.found is not None:
            snap["found"] = self.found
        return snap
