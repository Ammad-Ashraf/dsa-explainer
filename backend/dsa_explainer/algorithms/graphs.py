"""Graph algorithms: breadth-first search, depth-first search, Dijkstra, topological sort.

All of them take neighbours in alphabetical (or numeric) order, so every run,
narration and quiz answer is deterministic.
"""

from __future__ import annotations

from .base import MAX_ITEMS, OpError, Structure, as_int, natural_key, normalize


def _label(x) -> str:
    s = str(x).strip()
    if not 0 < len(s) <= 3:
        raise OpError(f"node label {x!r} must be 1 to 3 characters")
    return s


class _Graph(Structure):
    CATEGORY = "graphs"
    NOUN = "nodes"
    VIEW = "graph"
    WEIGHTED = False
    DIRECTED_DEFAULT = False
    NEEDS_START = True

    def __init__(self, initial) -> None:
        super().__init__()
        example = '{"edges": [["A", "B"], ["A", "C"]]' + (', "start": "A"}' if self.NEEDS_START else "}")
        if not isinstance(initial, dict) or "edges" not in initial or (self.NEEDS_START and "start" not in initial):
            raise OpError(f"initial data for {self.TITLE.lower()} must look like {example}")
        self.directed = bool(initial.get("directed", self.DIRECTED_DEFAULT))
        self.adj: dict[str, set[str]] = {}
        self.weights: dict[tuple[str, str], int] = {}
        for n in initial.get("nodes") or []:
            self.adj.setdefault(_label(n), set())
        for e in initial["edges"]:
            size = 3 if self.WEIGHTED else 2
            if not isinstance(e, (list, tuple)) or len(e) != size:
                pair = '["A", "B", 4]' if self.WEIGHTED else '["A", "B"]'
                raise OpError(f"edge {e!r} must look like {pair}")
            a, b = _label(e[0]), _label(e[1])
            if a == b:
                raise OpError(f"edge {e!r} joins a node to itself")
            if b in self.adj.get(a, ()):  # also catches B-C after C-B in an undirected graph
                raise OpError(f"the edge between {a} and {b} is given twice")
            self.adj.setdefault(a, set()).add(b)
            self.adj.setdefault(b, set())
            if self.WEIGHTED:
                w = as_int(e[2], "an edge weight", 1, 99)
                self.weights[(a, b)] = w
                if not self.directed:
                    self.weights[(b, a)] = w
            if not self.directed:
                self.adj[b].add(a)
        if len(self.adj) > MAX_ITEMS + 1:
            raise OpError(f"keep the graph to at most {MAX_ITEMS + 1} nodes")
        self.hot: list[list[str]] = []  # edges the last operation used, for the picture
        if self.NEEDS_START:
            self.start = _label(initial["start"])
            if self.start not in self.adj:
                raise OpError(f"start node {self.start} is not in the graph")

    def neighbours(self, n: str) -> list[str]:
        return sorted(self.adj[n], key=natural_key)

    def values(self) -> set[str]:
        return {normalize(n) for n in self.adj} | {normalize(w) for w in self.weights.values()}

    def _edges(self) -> list[list]:
        nodes = sorted(self.adj, key=natural_key)
        if self.directed:
            pairs = [(a, b) for a in nodes for b in self.neighbours(a)]
        else:
            pairs = [(a, b) for a in nodes for b in self.neighbours(a) if natural_key(a) < natural_key(b)]
        return [[a, b, self.weights[(a, b)]] if self.WEIGHTED else [a, b] for a, b in pairs]

    def _base_snapshot(self) -> dict:
        return {"nodes": sorted(self.adj, key=natural_key), "edges": self._edges(), "directed": self.directed,
                "weighted": self.WEIGHTED, "start": getattr(self, "start", None), "hot_edges": list(self.hot)}


class BFS(_Graph):
    NAME, TITLE = "bfs", "Breadth-first search"
    SUMMARY = "Explore a graph ring by ring, using a queue of nodes to visit."
    DESCRIPTION = ("Breadth-first search visits the start node, then all its neighbours, then their neighbours, "
                   "and so on. A queue remembers who is waiting, so nodes are visited in order of distance. It "
                   "finds shortest paths when every edge counts the same.")
    COMPLEXITY = {"best": "O(V + E)", "average": "O(V + E)", "worst": "O(V + E)", "space": "O(V)"}
    PSEUDOCODE = ("queue = [start]", "repeat: n = dequeue; visit(n)",
                  "    enqueue every neighbour of n that is not visited or queued")
    KEYWORDS = ("bfs", "breadth-first", "breadth first", "level by level", "shortest path unweighted")
    PRESETS = {"small graph": {"edges": [["A", "B"], ["A", "C"], ["B", "D"], ["C", "E"], ["D", "E"]], "start": "A"},
               "a line": {"edges": [["A", "B"], ["B", "C"], ["C", "D"]], "start": "A"},
               "a star": {"edges": [["A", "B"], ["A", "C"], ["A", "D"], ["A", "E"]], "start": "A"}}
    OPS = {"bfs_step": ()}
    FACTS = ("current", "queue", "visited", "bfs_order", "size")
    HELP = (
        'bfs (breadth-first search; also called graph): initial = {"edges": [["A", "B"], ["A", "C"]], "start": "A", '
        '"directed": false}, short node labels. ops: bfs_step() takes the node at the front of the queue, '
        "marks it visited, then adds its neighbours that are neither visited nor already queued to the back "
        "of the queue, in alphabetical (or numeric) order. Before the first step the queue holds only the "
        'start node. state = {"current": the node just taken, "queue": [front ... back], "visited": [nodes '
        'in the order they were taken]}. facts: current, queue, visited, bfs_order (the full BFS order), '
        "size (number of nodes)."
    )

    def __init__(self, initial) -> None:
        super().__init__(initial)
        self.current: str | None = None
        self.queue: list[str] = [self.start]
        self.visited: list[str] = []

    def op_bfs_step(self):
        if not self.queue:
            raise OpError("BFS is finished: the queue is empty")
        self.current = self.queue.pop(0)
        self.visited.append(self.current)
        added = [m for m in self.neighbours(self.current) if m not in self.visited and m not in self.queue]
        self.queue += added
        self.hot = [[self.current, m] for m in added]
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

    def facts(self) -> dict:
        return {**self.state(), "bfs_order": self.bfs_order(), "size": len(self.adj)}

    def snapshot(self) -> dict:
        return {**self._base_snapshot(), "current": self.current, "visited": list(self.visited),
                "frontier": {"name": "queue", "items": list(self.queue)}, **self.state()}


class DFS(_Graph):
    NAME, TITLE = "dfs", "Depth-first search"
    DIFFICULTY = "intermediate"
    SUMMARY = "Go as deep as you can, then back up: a stack remembers the way back."
    DESCRIPTION = ("Depth-first search follows one path as far as it goes, then backs up to the most recent node "
                   "that still has an unvisited neighbour. The stack of nodes on the current path is exactly the "
                   "call stack of the recursive version. It finds connected parts, cycles and orderings.")
    COMPLEXITY = {"best": "O(V + E)", "average": "O(V + E)", "worst": "O(V + E)", "space": "O(V)"}
    PSEUDOCODE = ("dfs(n): visit(n)", "    for each neighbour m of n, in order:", "        if m is not visited: dfs(m)")
    KEYWORDS = ("dfs", "depth-first", "depth first", "backtrack", "maze")
    PRESETS = {"small graph": {"edges": [["A", "B"], ["A", "C"], ["B", "D"], ["C", "E"], ["D", "E"]], "start": "A"},
               "a tree": {"edges": [["A", "B"], ["A", "C"], ["B", "D"], ["B", "E"], ["C", "F"]], "start": "A"},
               "with a cycle": {"edges": [["A", "B"], ["B", "C"], ["C", "A"], ["C", "D"]], "start": "A"}}
    OPS = {"dfs_step": ()}
    FACTS = ("current", "stack", "top", "visited", "dfs_order", "size")
    HELP = (
        'dfs (depth-first search, recursive order): initial = {"edges": [["A", "B"], ["A", "C"]], "start": "A", '
        '"directed": false}. ops: dfs_step() visits the next node: the first step visits the start node; each '
        "later step goes to the smallest unvisited neighbour of the node on top of the stack, first popping "
        "(backing up from) every node that has no unvisited neighbour left. "
        'state = {"current": the node just visited, "stack": [start ... top], the path being explored, '
        '"visited": [nodes in visiting order]}. facts: current, stack, top (top of the stack), visited, '
        "dfs_order (the full DFS order), size (number of nodes)."
    )

    def __init__(self, initial) -> None:
        super().__init__(initial)
        self.current: str | None = None
        self.stack: list[str] = []
        self.visited: list[str] = []

    def _next_from(self, n: str) -> str | None:
        return next((m for m in self.neighbours(n) if m not in self.visited), None)

    def op_dfs_step(self):
        if not self.visited:
            self.current = self.start
            self.stack = [self.start]
            self.visited = [self.start]
            return [self.start]
        backed, depth = [], len(self.stack)
        while depth and self._next_from(self.stack[depth - 1]) is None:
            backed.append(self.stack[depth - 1])
            depth -= 1
        if depth == 0:  # nothing changes: an impossible operation leaves the state as it was
            raise OpError("DFS is finished: every node reachable from the start was visited")
        self.stack = self.stack[:depth]
        nxt = self._next_from(self.stack[-1])
        self.stack.append(nxt)
        self.visited.append(nxt)
        self.current = nxt
        self.hot = [[self.stack[-2], nxt]]
        return backed + [nxt]

    def dfs_order(self) -> list[str]:
        order: list[str] = []

        def go(n):
            order.append(n)
            for m in self.neighbours(n):
                if m not in order:
                    go(m)

        go(self.start)
        return order

    def state(self):
        return {"current": self.current, "stack": list(self.stack), "visited": list(self.visited)}

    def matches(self, claimed) -> bool:
        if not isinstance(claimed, dict):
            return False
        return normalize({k: claimed.get(k) for k in ("current", "stack", "visited")}) == normalize(self.state())

    def facts(self) -> dict:
        return {**self.state(), "top": self.stack[-1] if self.stack else None, "dfs_order": self.dfs_order(),
                "size": len(self.adj)}

    def snapshot(self) -> dict:
        return {**self._base_snapshot(), "current": self.current, "visited": list(self.visited),
                "frontier": {"name": "stack", "items": list(self.stack)}}


class Dijkstra(_Graph):
    NAME, TITLE = "dijkstra", "Dijkstra's shortest paths"
    DIFFICULTY = "advanced"
    WEIGHTED = True
    SUMMARY = "Settle the closest unsettled node, then relax its edges: shortest paths by weight."
    DESCRIPTION = ("Dijkstra's algorithm finds the shortest distance from a start node to every other node when "
                   "edge weights are not negative. It repeatedly settles the unsettled node with the smallest known "
                   "distance, then checks whether going through it gives any neighbour a shorter route.")
    COMPLEXITY = {"best": "O((V + E) log V)", "average": "O((V + E) log V)", "worst": "O((V + E) log V)",
                  "space": "O(V)"}
    PSEUDOCODE = ("dist[start] = 0; every other dist = infinity",
                  "repeat: u = the unsettled node with the smallest dist; settle u",
                  "    for each edge u to v with weight w: dist[v] = min(dist[v], dist[u] + w)")
    KEYWORDS = ("dijkstra", "shortest path", "shortest distance", "weighted graph", "weights")
    PRESETS = {"small map": {"edges": [["A", "B", 4], ["A", "C", 1], ["C", "B", 2], ["B", "D", 5], ["C", "D", 8]],
                             "start": "A"},
               "a triangle": {"edges": [["A", "B", 5], ["A", "C", 2], ["B", "C", 1]], "start": "A"},
               "five towns": {"edges": [["A", "B", 2], ["A", "C", 6], ["B", "C", 3], ["B", "D", 7], ["C", "E", 2],
                                        ["D", "E", 1]], "start": "A"}}
    OPS = {"settle": ()}
    FACTS = ("current", "settled", "distances", "size")
    HELP = (
        'dijkstra (shortest paths, non-negative weights): initial = {"edges": [["A", "B", 4], ["A", "C", 1]], '
        '"start": "A", "directed": false}, weights are whole numbers from 1 to 99. Before the first step the '
        "start node has distance 0 and every other node infinity (null). ops: settle() takes the unsettled node "
        "with the smallest finite distance (ties: alphabetical), settles it, and lowers each neighbour's "
        "distance if going through it is shorter. "
        'state = {"current": the node just settled, "settled": [nodes in settling order], '
        '"dist": {"A": 0, "B": 3, "C": null}} (null = infinity). '
        "facts: current, settled, distances (written like A=0, B=3, C=inf), size, and dist_<node> for each "
        "node, e.g. dist_B."
    )

    def __init__(self, initial) -> None:
        super().__init__(initial)
        self.dist: dict[str, int | None] = {n: None for n in self.adj}
        self.dist[self.start] = 0
        self.settled: list[str] = []
        self.current: str | None = None
        self.improved: list[str] = []

    def op_settle(self):
        open_nodes = [n for n in self.adj if n not in self.settled and self.dist[n] is not None]
        if not open_nodes:
            raise OpError("Dijkstra is finished: every reachable node is settled")
        u = min(open_nodes, key=lambda n: (self.dist[n], natural_key(n)))
        self.current = u
        self.settled.append(u)
        self.improved = []
        for v in self.neighbours(u):
            if v in self.settled:
                continue
            through = self.dist[u] + self.weights[(u, v)]
            if self.dist[v] is None or through < self.dist[v]:
                self.dist[v] = through
                self.improved.append(v)
        self.hot = [[u, v] for v in self.improved]
        return [u] + self.improved

    def _ordered_dist(self) -> dict:
        return {n: self.dist[n] for n in sorted(self.adj, key=natural_key)}

    def state(self):
        return {"current": self.current, "settled": list(self.settled), "dist": self._ordered_dist()}

    def matches(self, claimed) -> bool:
        if not isinstance(claimed, dict) or not isinstance(claimed.get("dist"), dict):
            return False
        dist = {str(k): (None if str(v).lower() in ("none", "null", "inf", "infinity") else v)
                for k, v in claimed["dist"].items()}
        mine = {"current": claimed.get("current"), "settled": claimed.get("settled"), "dist": dist}
        return normalize(mine) == normalize(self.state())

    def values(self) -> set[str]:
        return super().values() | {normalize(d) for d in self.dist.values() if d is not None}

    def facts(self) -> dict:
        distances = [f"{n}={'inf' if d is None else d}" for n, d in self._ordered_dist().items()]
        return {"current": self.current, "settled": list(self.settled), "distances": distances,
                "size": len(self.adj), **{f"dist_{n}": ("inf" if d is None else d) for n, d in self.dist.items()}}

    def snapshot(self) -> dict:
        return {**self._base_snapshot(), "current": self.current, "visited": list(self.settled),
                "labels": {n: ("∞" if d is None else str(d)) for n, d in self._ordered_dist().items()},
                "improved": list(self.improved), "frontier": {"name": "settled", "items": list(self.settled)}}


class TopologicalSort(_Graph):
    NAME, TITLE = "topological_sort", "Topological sort"
    DIFFICULTY = "advanced"
    DIRECTED_DEFAULT = True
    NEEDS_START = False
    SUMMARY = "Order tasks so every task comes after the ones it depends on (Kahn's algorithm)."
    DESCRIPTION = ("A topological order lists the nodes of a directed graph so that every edge points forward. "
                   "Kahn's algorithm keeps the nodes with no remaining incoming edges ready, takes one, and removes "
                   "its outgoing edges, which may make more nodes ready. Build systems and course prerequisites "
                   "use it.")
    COMPLEXITY = {"best": "O(V + E)", "average": "O(V + E)", "worst": "O(V + E)", "space": "O(V)"}
    PSEUDOCODE = ("ready = nodes with in-degree 0",
                  "repeat: n = the smallest ready node; append n to the order",
                  "    for each edge n to m: indegree[m] -= 1; if it is 0, m becomes ready")
    KEYWORDS = ("topological", "topo sort", "toposort", "kahn", "dependencies", "prerequisite", "dag")
    PRESETS = {"getting dressed": {"edges": [["A", "B"], ["A", "C"], ["B", "D"], ["C", "D"]]},
               "courses": {"edges": [["A", "C"], ["B", "C"], ["C", "D"], ["B", "E"]]},
               "a chain": {"edges": [["A", "B"], ["B", "C"], ["C", "D"]]}}
    OPS = {"take": ()}
    FACTS = ("current", "ready", "order", "size")
    HELP = (
        'topological_sort (Kahn\'s algorithm, directed graph): initial = {"edges": [["A", "B"], ["A", "C"]]} where '
        '["A", "B"] means A must come before B. Before the first step, every node with no incoming edges is '
        "ready. ops: take() removes the alphabetically smallest ready node, appends it to the order, and deletes "
        "its outgoing edges; nodes left with no incoming edges become ready. "
        'state = {"current": the node just taken, "ready": [ready nodes, alphabetical], "order": [nodes taken]}. '
        "facts: current, ready, order, size."
    )

    def __init__(self, initial) -> None:
        if isinstance(initial, dict):
            initial = {**initial, "directed": True}
        super().__init__(initial)
        self.indegree = {n: 0 for n in self.adj}
        for a in self.adj:
            for b in self.adj[a]:
                self.indegree[b] += 1
        self.ready = sorted((n for n, d in self.indegree.items() if d == 0), key=natural_key)
        self.order: list[str] = []
        self.current: str | None = None
        if not self.ready:
            raise OpError("every node has an incoming edge, so the graph has a cycle and no topological order")

    def op_take(self):
        if not self.ready:
            if len(self.order) < len(self.adj):
                raise OpError("no node is ready but some are left: the graph has a cycle")
            raise OpError("the topological sort is finished")
        n = self.ready.pop(0)
        self.current = n
        self.order.append(n)
        freed = []
        for m in self.neighbours(n):
            self.indegree[m] -= 1
            if self.indegree[m] == 0:
                freed.append(m)
        self.ready = sorted(self.ready + freed, key=natural_key)
        self.hot = [[n, m] for m in self.neighbours(n)]
        return [n] + freed

    def state(self):
        return {"current": self.current, "ready": list(self.ready), "order": list(self.order)}

    def matches(self, claimed) -> bool:
        if not isinstance(claimed, dict):
            return False
        return normalize({k: claimed.get(k) for k in ("current", "ready", "order")}) == normalize(self.state())

    def facts(self) -> dict:
        return {**self.state(), "size": len(self.adj)}

    def snapshot(self) -> dict:
        return {**self._base_snapshot(), "current": self.current, "visited": list(self.order),
                "labels": {n: f"in {d}" for n, d in self.indegree.items() if n not in self.order},
                "frontier": {"name": "ready", "items": list(self.ready)},
                "done_row": {"name": "order", "items": list(self.order)}}
