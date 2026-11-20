"""Graphs: BFS, DFS, Dijkstra and topological sort share one picture.

Nodes are laid out in rows by distance from the start (or by dependency depth
when there is no start). Under the graph, up to two rows of tokens show the
algorithm's frontier (queue, stack, ready set) and what is done (visited,
settled, order). Weighted graphs show each weight on its edge; per-node labels
(distances, in-degrees) sit beside the nodes.
"""

from __future__ import annotations

import numpy as np
from manim import Circle, VGroup

from ...algorithms.base import natural_key
from .common import (
    ACCENT,
    CURRENT,
    DOWN,
    EDGE,
    FG,
    LEFT,
    LINE,
    MUTED,
    QUEUED,
    RIGHT,
    UP,
    VISITED,
    View,
    cell,
    label,
    link,
    node,
)


def graph_positions(snap: dict) -> dict:
    """Rows by BFS distance from the start (or from the nodes with no incoming edges)."""
    adj = {n: [] for n in snap["nodes"]}
    indeg = {n: 0 for n in snap["nodes"]}
    for e in snap["edges"]:
        a, b = e[0], e[1]
        adj[a].append(b)
        indeg[b] += 1
        if not snap["directed"]:
            adj[b].append(a)
    starts = [snap["start"]] if snap.get("start") else [n for n in snap["nodes"] if indeg[n] == 0][:3]
    level = {s: 0 for s in starts}
    order = list(starts)
    for n in order:  # the list grows while we walk it: a BFS
        for m in sorted(adj[n], key=natural_key):
            if m not in level:
                level[m] = level[n] + 1
                order.append(m)
    last = max(level.values(), default=-1) + 1
    order += [n for n in snap["nodes"] if n not in level]
    rows: dict[int, list] = {}
    for n in order:
        rows.setdefault(level.get(n, last), []).append(n)
    dy = min(1.4, 3.0 / max(1, len(rows) - 1))
    pos = {}
    for r, lvl in enumerate(sorted(rows)):
        row = rows[lvl]
        dx = min(3.4, 10.5 / len(row))
        for i, n in enumerate(row):
            pos[n] = np.array([(i - (len(row) - 1) / 2) * dx, 2.5 - r * dy, 0])
    return pos


class GraphView(View):
    name = "graph"

    def draw(self, snap, marks):
        mobs, pos = {}, graph_positions(snap)
        frontier = snap.get("frontier") or {"name": "queue", "items": snap.get("queue", [])}
        visited = snap.get("visited", [])
        hot = {tuple(e) for e in snap.get("hot_edges", [])}
        if not snap["directed"]:
            hot |= {(b, a) for a, b in hot}

        def colour(n):
            if n == snap.get("current"):
                return CURRENT
            if n in visited:
                return VISITED
            return QUEUED if n in frontier["items"] else EDGE

        for e in snap["edges"]:
            a, b = e[0], e[1]
            mobs[("edge", a, b)] = link(pos[a], pos[b], color=ACCENT if (a, b) in hot else LINE,
                                        arrow=snap["directed"])
            if snap.get("weighted"):
                mid = (pos[a] + pos[b]) / 2
                normal = np.array([-(pos[b] - pos[a])[1], (pos[b] - pos[a])[0], 0])
                normal = normal / (np.linalg.norm(normal) or 1) * 0.28
                mobs[("weight", a, b)] = label(e[2], 22, ACCENT if (a, b) in hot else MUTED).move_to(mid + normal)
        for n in snap["nodes"]:
            mobs[("node", n)] = node(n, colour(n)).move_to(pos[n])
        for n, text in (snap.get("labels") or {}).items():  # distances, in-degrees: a small tag above the node
            hot_label = n in snap.get("improved", [])
            tag = label(text, 22, ACCENT if hot_label else FG if text != "∞" else MUTED, bold=True)
            mobs[("label", n, text)] = tag.next_to(mobs[("node", n)], UP, buff=0.06)

        rows = [(frontier["name"], frontier["items"], VISITED if frontier["name"] == "settled" else QUEUED)]
        done = snap.get("done_row") or {"name": "visited", "items": visited}
        if frontier["name"] != "settled":
            rows.append((done["name"], done["items"], VISITED))
        slide = frontier["name"] == "queue"  # BFS: a dequeued token slides down into the visited row
        for y, (name, items, col) in zip((-1.85, -2.65), rows):
            mobs[("row", name)] = label(name, 24, col).move_to([-5.3, y, 0])
            for i, n in enumerate(items):
                key = ("token", n) if slide else ("token", name, n)
                mobs[key] = cell(n, 0.72, 0.6, col).move_to([-4.0 + i * 0.86, y, 0])
        legend = [(CURRENT, "current"), (QUEUED, f"in {frontier['name']}" if frontier["name"] != "settled" else
                                         "reached"), (VISITED, done["name"] if frontier["name"] != "settled" else
                                                      "settled")]
        mobs["legend"] = VGroup(*[
            VGroup(Circle(radius=0.11, color=col, stroke_width=4), label(text, 20, MUTED)).arrange(RIGHT, buff=0.15)
            for col, text in legend
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([5.4, -2.2, 0])
        return mobs

    def focus_key(self, element):
        return ("node", element)

    def marks(self, job, before_keys):
        return {}  # node colours come from the state; hot edges from the simulator

    def path(self, job, shown):
        if not job["focus"]:
            return []
        first = job["focus"][0]
        token = ("token", first)
        return [token] if token in shown else [k for k in (("node", first),) if k in shown]

