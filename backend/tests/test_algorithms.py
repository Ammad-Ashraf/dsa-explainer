"""Every simulator against an independent reference implementation, on random inputs (Hypothesis).

The simulators are what the verifier trusts, so they are tested hardest: a bug
here would let a wrong video through.
"""

import bisect
import heapq
from collections import deque

import pytest
from dsa_explainer import algorithms
from dsa_explainer.algorithms import OpError, build
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

settings.register_profile("dsa", max_examples=60, deadline=None, suppress_health_check=[HealthCheck.too_slow])
settings.load_profile("dsa")

small_ints = st.integers(min_value=1, max_value=99)
arrays = st.lists(small_ints, min_size=1, max_size=8)


def run_all(ds, op, limit=50):
    steps = 0
    while steps < limit:
        try:
            ds.run(op)
        except OpError:
            return steps
        steps += 1
    raise AssertionError(f"{op} never finished")


# --- linear structures ------------------------------------------------------------------


@given(st.lists(st.tuples(st.sampled_from(["push", "pop", "peek"]), small_ints), max_size=20))
def test_stack_matches_a_python_list(ops):
    ds, ref = build("stack", []), []
    for op, v in ops:
        if op == "push":
            if len(ref) >= algorithms.MAX_ITEMS:
                with pytest.raises(OpError):
                    ds.run("push", {"value": v})
                continue
            ds.run("push", {"value": v})
            ref.append(v)
        elif not ref:
            with pytest.raises(OpError):
                ds.run(op)
        else:
            ds.run(op)
            if op == "pop":
                ref.pop()
        assert ds.state() == ref and ds.facts()["top"] == (ref[-1] if ref else None)


@given(st.lists(st.tuples(st.sampled_from(["push_front", "push_back", "pop_front", "pop_back"]), small_ints),
                max_size=20))
def test_deque_matches_collections_deque(ops):
    ds, ref = build("deque", []), deque()
    for op, v in ops:
        if op.startswith("push"):
            if len(ref) >= algorithms.MAX_ITEMS:
                continue
            ds.run(op, {"value": v})
            ref.appendleft(v) if op == "push_front" else ref.append(v)
        elif not ref:
            with pytest.raises(OpError):
                ds.run(op)
        else:
            ds.run(op)
            ref.popleft() if op == "pop_front" else ref.pop()
        assert ds.state() == list(ref)
        assert ds.facts()["front"] == (ref[0] if ref else None) and ds.facts()["rear"] == (ref[-1] if ref else None)


@given(st.lists(small_ints, max_size=6, unique=True), st.lists(small_ints, max_size=6))
def test_linked_list_insert_and_delete(values, deletes):
    ds, ref = build("linked_list", values), list(values)
    for v in deletes:
        if v in ref:
            path = ds.run("delete", {"value": v})
            assert len(path) == ref.index(v) + 1  # walked from the head to the node
            ref.remove(v)
        else:
            with pytest.raises(OpError):
                ds.run("delete", {"value": v})
        assert ds.state() == ref


# --- trees and heaps ----------------------------------------------------------------------


def bst_ok(tree, low=-10**9, high=10**9) -> bool:
    if tree is None:
        return True
    v = tree["value"]
    return low < v < high and bst_ok(tree["left"], low, v) and bst_ok(tree["right"], v, high)


@given(st.lists(small_ints, max_size=7, unique=True), st.lists(small_ints, max_size=5))
def test_bst_stays_a_search_tree(values, deletes):
    ds = build("bst", values)
    present = set(values)
    for v in deletes:
        if v in present:
            ds.run("delete", {"value": v})
            present.discard(v)
        assert bst_ok(ds.state())
        assert ds.facts()["inorder"] == sorted(present)


@given(st.lists(small_ints, min_size=1, max_size=7, unique=True), st.sampled_from(algorithms.trees.ORDERS))
def test_traversal_visits_every_node_once_in_order(values, order):
    ds = build("tree_traversal", {"values": values, "order": order})
    steps = run_all(ds, "visit")
    assert steps == len(values)
    visited = ds.state()["visited"]
    assert sorted(visited) == sorted(values) and visited == ds.facts()["order"]
    if order == "inorder":
        assert visited == sorted(values)
    if order == "preorder":
        assert visited[0] == values[0]  # the first value inserted is the root
    if order == "postorder":
        assert visited[-1] == values[0]


@given(st.lists(st.one_of(small_ints, st.none()), max_size=14))
def test_min_heap_matches_heapq(ops):
    ds, ref = build("min_heap", []), []
    for v in ops:
        if v is None:  # extract
            if not ref:
                with pytest.raises(OpError):
                    ds.run("extract_min")
                continue
            ds.run("extract_min")
            heapq.heappop(ref)
        elif len(ref) < algorithms.MAX_ITEMS:
            ds.run("insert", {"value": v})
            heapq.heappush(ref, v)
        a = ds.state()
        assert sorted(a) == sorted(ref)
        assert all(a[(i - 1) // 2] <= a[i] for i in range(1, len(a)))  # the heap property
        assert ds.facts()["root"] == (min(ref) if ref else None)


@given(st.lists(small_ints, min_size=1, max_size=7))
def test_heap_sort_sorts(values):
    ds = build("heap_sort", values)
    with pytest.raises(OpError):
        ds.run("extract_max")  # the heap must be built first
    ds.run("build_heap")
    a = ds.state()["array"]
    assert all(a[(i - 1) // 2] >= a[i] for i in range(1, len(a)))  # a max-heap
    steps = run_all(ds, "extract_max")
    assert steps == len(values) - 1 and ds.state()["array"] == sorted(values)


# --- sorting and searching ----------------------------------------------------------------

SORTS = {"bubble_sort": "bubble_pass", "insertion_sort": "insert_next", "selection_sort": "select_next",
         "merge_sort": "merge_next", "quick_sort": "partition_next"}


@pytest.mark.parametrize("name", SORTS)
@given(values=arrays)
def test_every_sort_sorts(name, values):
    ds = build(name, values)
    steps = run_all(ds, SORTS[name])
    assert ds.state() == sorted(values)
    assert steps <= len(values) * 2  # a lesson can show it in a handful of steps
    if name != "merge_sort":
        assert ds.facts()["sorted_count"] == len(values)


@given(arrays)
def test_bubble_pass_places_the_largest_unsorted_value(values):
    ds = build("bubble_sort", values)
    for k in range(1, len(values)):
        try:
            ds.run("bubble_pass")
        except OpError:
            break
        a = ds.state()
        assert a[len(a) - k:] == sorted(values)[len(a) - k:]


@given(arrays)
def test_quick_sort_partition_puts_the_pivot_in_place(values):
    ds = build("quick_sort", values)
    while True:
        try:
            ds.run("partition_next")
        except OpError:
            break
        f, a = ds.facts(), ds.state()
        i = f["pivot_index"]
        assert a[i] == f["pivot"] == sorted(values)[i]
        assert all(x < f["pivot"] for x in a[f["low"]:i]) and all(x >= f["pivot"] for x in a[i + 1:f["high"] + 1])


@given(arrays, small_ints)
def test_linear_search_matches_list_index(values, target):
    ds = build("linear_search", {"array": values, "target": target})
    steps = run_all(ds, "check_next")
    if target in values:
        assert ds.state()["found"] and ds.state()["index"] == values.index(target) and steps == values.index(target) + 1
    else:
        assert not ds.state()["found"] and steps == len(values)


@given(st.lists(small_ints, min_size=1, max_size=8, unique=True), small_ints)
def test_binary_search_matches_bisect(values, target):
    values = sorted(values)
    ds = build("binary_search", {"array": values, "target": target})
    steps = run_all(ds, "probe")
    i = bisect.bisect_left(values, target)
    found = i < len(values) and values[i] == target
    assert ds.state()["found"] == found
    if found:
        assert values[ds.state()["mid"]] == target
    assert steps <= len(values).bit_length()  # it halves the range every time


def test_binary_search_refuses_an_unsorted_array():
    with pytest.raises(OpError):
        build("binary_search", {"array": [3, 1, 2], "target": 2})


# --- graphs ---------------------------------------------------------------------------------

LABELS = "ABCDEFGH"


@st.composite
def graphs(draw, weighted=False, connected_from_a=True):
    n = draw(st.integers(min_value=2, max_value=7))
    nodes = list(LABELS[:n])
    edges = set()
    if connected_from_a:  # a spanning tree from A keeps every node reachable
        for i in range(1, n):
            edges.add((nodes[draw(st.integers(0, i - 1))], nodes[i]))
    extra = draw(st.lists(st.tuples(st.sampled_from(nodes), st.sampled_from(nodes)), max_size=6))
    for a, b in extra:  # one edge per pair of nodes, in either direction
        if a != b and (a, b) not in edges and (b, a) not in edges:
            edges.add((a, b))
    out = sorted(edges)
    if weighted:
        out = [[a, b, draw(st.integers(1, 20))] for a, b in out]
    else:
        out = [[a, b] for a, b in out]
    return {"edges": out, "start": "A", "nodes": nodes}


def adjacency(g, directed=False):
    adj = {n: set() for n in g["nodes"]}
    for e in g["edges"]:
        adj[e[0]].add(e[1])
        if not directed:
            adj[e[1]].add(e[0])
    return {n: sorted(v) for n, v in adj.items()}


@given(graphs())
def test_bfs_visits_in_breadth_first_order(g):
    adj, order, queue = adjacency(g), [], ["A"]
    while queue:
        n = queue.pop(0)
        order.append(n)
        queue += [m for m in adj[n] if m not in order and m not in queue]
    ds = build("bfs", g)
    run_all(ds, "bfs_step")
    assert ds.state()["visited"] == order == ds.facts()["bfs_order"]


@given(graphs())
def test_dfs_visits_in_recursive_order(g):
    adj, order = adjacency(g), []

    def go(n):
        order.append(n)
        for m in adj[n]:
            if m not in order:
                go(m)

    go("A")
    ds = build("dfs", g)
    run_all(ds, "dfs_step")
    assert ds.state()["visited"] == order == ds.facts()["dfs_order"]


@given(graphs(weighted=True))
def test_dijkstra_matches_bellman_ford(g):
    dist = {n: None for n in g["nodes"]}
    dist["A"] = 0
    for _ in g["nodes"]:
        for a, b, w in g["edges"]:
            for x, y in ((a, b), (b, a)):
                if dist[x] is not None and (dist[y] is None or dist[x] + w < dist[y]):
                    dist[y] = dist[x] + w
    ds = build("dijkstra", g)
    steps = run_all(ds, "settle")
    assert steps == len(g["nodes"]) and ds.state()["dist"] == {n: dist[n] for n in sorted(dist)}
    settled = ds.state()["settled"]
    assert [dist[n] for n in settled] == sorted(dist[n] for n in settled)  # settled in order of distance


@given(st.integers(2, 7).flatmap(lambda n: st.lists(st.tuples(st.integers(0, n - 1), st.integers(0, n - 1)),
                                                     max_size=10).map(lambda pairs: (n, pairs))))
def test_topological_sort_orders_a_dag(case):
    n, pairs = case
    nodes = list(LABELS[:n])
    edges = sorted({(nodes[min(a, b)], nodes[max(a, b)]) for a, b in pairs if a != b})  # low to high: no cycles
    ds = build("topological_sort", {"edges": [list(e) for e in edges], "nodes": nodes})
    run_all(ds, "take")
    order = ds.state()["order"]
    assert sorted(order) == nodes
    assert all(order.index(a) < order.index(b) for a, b in edges)


def test_an_edge_given_twice_is_refused():
    with pytest.raises(OpError, match="twice"):
        build("dijkstra", {"edges": [["A", "B", 1], ["B", "A", 2]], "start": "A"})
    with pytest.raises(OpError, match="twice"):
        build("bfs", {"edges": [["A", "B"], ["A", "B"]], "start": "A"})
    build("topological_sort", {"edges": [["A", "B"], ["B", "C"]]})  # directed: A-B and B-A would differ


def test_topological_sort_reports_a_cycle():
    ds = build("topological_sort", {"edges": [["A", "B"], ["B", "C"], ["C", "B"]]})
    ds.run("take")
    with pytest.raises(OpError, match="cycle"):
        ds.run("take")


# --- hashing and dynamic programming --------------------------------------------------------


@given(st.integers(2, 7), st.lists(st.tuples(st.sampled_from(["insert", "delete", "search"]),
                                             st.integers(0, 60)), max_size=15))
def test_hash_table_matches_a_dict_of_chains(m, ops):
    ds, ref = build("hash_table", {"buckets": m, "keys": []}), [[] for _ in range(m)]
    for op, k in ops:
        chain = ref[k % m]
        if op == "insert":
            if k in chain or sum(map(len, ref)) >= algorithms.MAX_ITEMS:
                with pytest.raises(OpError):
                    ds.run("insert", {"key": k})
                continue
            ds.run("insert", {"key": k})
            chain.append(k)
        elif op == "delete":
            if k not in chain:
                with pytest.raises(OpError):
                    ds.run("delete", {"key": k})
                continue
            ds.run("delete", {"key": k})
            chain.remove(k)
        else:
            ds.run("search", {"key": k})
            assert ds.facts()["found"] == (k in chain)
        assert ds.state() == ref and ds.facts()["bucket"] == k % m


@given(st.integers(2, 10))
def test_fibonacci_table(n):
    ds = build("fibonacci", {"n": n})
    run_all(ds, "fill_next")
    fib = [0, 1]
    while len(fib) <= n:
        fib.append(fib[-1] + fib[-2])
    assert ds.state() == fib


@given(st.lists(st.integers(1, 9), min_size=1, max_size=4, unique=True), st.integers(2, 10))
def test_coin_change_matches_reference(coins, amount):
    best = [0] + [None] * amount
    for a in range(1, amount + 1):
        options = [best[a - c] + 1 for c in coins if c <= a and best[a - c] is not None]
        best[a] = min(options) if options else None
    ds = build("coin_change", {"coins": coins, "amount": amount})
    run_all(ds, "fill_next")
    assert ds.state() == ["inf" if b is None else b for b in best]


# --- the registry ---------------------------------------------------------------------------


@pytest.mark.parametrize("cls", algorithms.ALL, ids=lambda c: c.NAME)
def test_every_algorithm_is_fully_described(cls):
    info = cls.info()
    for field in ("title", "category", "difficulty", "summary", "description", "view"):
        assert info[field], field
    assert cls.CATEGORY in algorithms.CATEGORIES and cls.DIFFICULTY in ("beginner", "intermediate", "advanced")
    assert set(cls.COMPLEXITY) == {"best", "average", "worst", "space"} and cls.PSEUDOCODE and cls.KEYWORDS
    assert cls.HELP.startswith(cls.NAME) and "size" in cls.FACTS
    assert len(cls.PRESETS) >= 2
    for preset in cls.PRESETS.values():
        ds = cls(preset)
        assert "size" in ds.facts()
        ds.snapshot()


@pytest.mark.parametrize("topic, expected", [
    ("How does a stack work?", ["stack"]),
    ("Show how a queue handles print jobs", ["queue"]),
    ("deque with both ends", ["deque"]),
    ("bubble sort on 5 1 4 2", ["bubble_sort"]),
    ("binary search for 7 in a sorted array", ["binary_search"]),
    ("Dijkstra shortest path from A", ["dijkstra"]),
    ("in-order traversal of a tree", ["tree_traversal"]),
    ("explain quicksort partitioning with a pivot", ["quick_sort"]),
    ("what is the meaning of life", []),
])
def test_topics_route_to_the_right_algorithm(topic, expected):
    assert [cls.NAME for cls in algorithms.candidates(topic)] == expected


def test_the_old_graph_name_still_works():
    assert algorithms.get("graph") is algorithms.BFS and algorithms.DISPLAY_NAMES["graph"] == "Breadth-first search"


# --- what the video shows beside the picture: counts, the facts strip, pseudocode lines ------


@given(arrays)
def test_insertion_and_selection_counts_match_an_instrumented_reference(values):
    a, steps = list(values), []
    for i in range(1, len(a)):  # textbook insertion sort, counting every comparison with the key
        key, j, comparisons = a[i], i - 1, 0
        while j >= 0:
            comparisons += 1
            if a[j] <= key:
                break
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
        steps.append(comparisons)
    ds = build("insertion_sort", values)
    for expected in steps:
        ds.run("insert_next")
        assert ds.facts()["comparisons"] == expected
    ds = build("selection_sort", values)
    for k in range(len(values) - 1):
        ds.run("select_next")
        assert ds.facts()["comparisons"] == len(values) - k - 1


@given(arrays)
def test_quick_sort_counts_match_an_instrumented_lomuto(values):
    a, log, pending = list(values), [], [(0, len(values) - 1)] if len(values) > 1 else []
    while pending:
        lo, hi = pending.pop()
        i, swaps = lo, 0
        for j in range(lo, hi):
            if a[j] < a[hi]:
                swaps += i != j
                a[i], a[j] = a[j], a[i]
                i += 1
        swaps += i != hi
        a[i], a[hi] = a[hi], a[i]
        log.append((hi - lo, swaps))
        pending += [r for r in ((i + 1, hi), (lo, i - 1)) if r[1] - r[0] >= 1]
    ds = build("quick_sort", values)
    for comparisons, swaps in log:
        ds.run("partition_next")
        assert (ds.facts()["comparisons"], ds.facts()["swaps"]) == (comparisons, swaps)
    assert ds.state() == sorted(values)


@given(st.lists(small_ints, max_size=7))
def test_heap_swap_counts_match_the_sift_distance(values):
    ds, heap = build("min_heap", []), []
    for v in values:
        heap.append(v)
        i, swaps = len(heap) - 1, 0
        while i and heap[i] < heap[(i - 1) // 2]:
            heap[i], heap[(i - 1) // 2] = heap[(i - 1) // 2], heap[i]
            i, swaps = (i - 1) // 2, swaps + 1
        ds.run("insert", {"value": v})
        assert ds.facts()["swaps"] == swaps and ds.state() == heap


@given(st.lists(small_ints, min_size=1, max_size=8, unique=True), small_ints)
def test_search_comparisons_count_the_values_checked(values, target):
    ds = build("linear_search", {"array": values, "target": target})
    steps = run_all(ds, "check_next")
    assert ds.facts()["comparisons"] == steps == (values.index(target) + 1 if target in values else len(values))
    values = sorted(values)
    ds = build("binary_search", {"array": values, "target": target})
    assert ds.facts()["comparisons"] == 0
    steps = run_all(ds, "probe")
    assert ds.facts()["comparisons"] == steps <= len(values).bit_length()


@pytest.mark.parametrize("cls", algorithms.ALL, ids=lambda c: c.NAME)
def test_strip_and_pseudocode_lines_come_from_the_simulator(cls):
    assert cls.STRIP and set(cls.STRIP) <= set(cls.FACTS), "the strip shows only declared facts"
    assert cls.PSEUDOCODE and set(cls.OP_LINES) == set(cls.OPS), "every operation names its pseudocode lines"
    for preset in cls.PRESETS.values():
        ds = cls(preset)
        for _ in range(4):
            ran = False
            for op, needs in cls.OPS.items():
                try:
                    ds.run(op, {a: {"value": 42, "key": 11, "index": 0}[a] for a in needs})
                except OpError:
                    continue
                lines = ds.code_lines(op)
                assert lines and all(0 <= i < len(cls.PSEUDOCODE) for i in lines), (op, lines)
                assert set(lines) <= set(cls.OP_LINES[op]), "the lines a step runs are among those its op declares"
                strip = ds.strip()
                assert [label for label, _ in strip] == [cls.FACT_LABELS.get(n, n.replace("_", " "))
                                                        for n in cls.STRIP if n in ds.facts()]
                facts = ds.facts()
                for (_, text), name in zip(strip, [n for n in cls.STRIP if n in facts]):
                    assert text == ("-" if facts[name] is None else algorithms.fact_text(facts[name]))
                ran = True
                break
            if not ran:
                break


def test_pseudocode_lines_follow_what_the_operation_did():
    ds = build("binary_search", {"array": [1, 3, 5, 7, 9], "target": 7})
    ds.run("probe")  # mid = 2, value 5 < 7: go right
    assert ds.code_lines("probe") == [2, 4]
    ds.run("probe")  # mid = 3, found
    assert ds.code_lines("probe") == [2, 3]
    ds = build("bubble_sort", [1, 2, 3])
    ds.run("bubble_pass")  # no swaps: the early stop line runs too
    assert ds.code_lines("bubble_pass") == [1, 2, 3]
    ds = build("tree_traversal", {"values": [2, 1, 3], "order": "postorder"})
    ds.run("visit")
    assert ds.code_lines("visit") == [2]
