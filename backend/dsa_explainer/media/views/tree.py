"""Binary trees (BST, traversals) and array heaps (min-heap, heap sort)."""

from __future__ import annotations

import math

import numpy as np

from .common import ACCENT, CURRENT, DOWN, EDGE, MUTED, VISITED, View, cell, label, link, node


class TreeView(View):
    name, enter, exit = "tree", DOWN * 0.4, DOWN * 0.4

    def draw(self, snap, marks):
        mobs, nodes, root = {}, snap["nodes"], snap["root"]
        nodes = {int(k): v for k, v in nodes.items()}  # ids may arrive as text after a JSON round trip
        if root is None:
            mobs["empty"] = label("empty tree", 26, MUTED).move_to([0, 1, 0])
            return mobs
        order, depth = [], {}

        def walk(nid, d):  # in-order position gives x, depth gives y
            if nid is not None:
                _, left, right = nodes[nid]
                walk(left, d + 1)
                order.append(nid)
                depth[nid] = d
                walk(right, d + 1)

        walk(root, 0)
        visited, current = snap.get("visited", []), snap.get("current")
        top = 2.35 if not visited else 2.55
        dx = min(1.5, 12.0 / len(order))
        dy = min(1.3, (4.9 if not visited else 3.6) / max(1, max(depth.values())))
        pos = {nid: np.array([(i - (len(order) - 1) / 2) * dx, top - depth[nid] * dy, 0]) for i, nid in enumerate(order)}
        for nid in order:
            value, left, right = nodes[nid]
            colour = marks.get(nid) or (CURRENT if nid == current else VISITED if nid in visited else EDGE)
            mobs[nid] = node(value, colour).move_to(pos[nid])
            for child in (left, right):
                if child is not None:
                    mobs[("edge", nid, child)] = link(pos[nid], pos[child])
        if "visited" in snap:  # a traversal: the visiting order so far, as a row
            mobs["order-label"] = label(snap.get("label", "visited"), 24, VISITED).move_to([-5.2, -2.45, 0])
            for i, nid in enumerate(visited):
                mobs[("visit", nid)] = cell(nodes[nid][0], 0.72, 0.6, VISITED).move_to([-3.9 + i * 0.86, -2.45, 0])
        return mobs


def heap_positions(n: int) -> list[np.ndarray]:
    """Complete-tree layout for array indices 0..n-1: level by level, evenly spread."""
    out = []
    levels = max(1, math.floor(math.log2(n)) + 1) if n else 1
    dy = min(1.15, 2.9 / max(1, levels - 1))
    for i in range(n):
        d = math.floor(math.log2(i + 1))
        k = i + 1 - 2 ** d  # position within the level
        x = ((k + 0.5) / 2 ** d - 0.5) * 11.0
        out.append(np.array([x, 2.6 - d * dy, 0]))
    return out


class HeapView(View):
    name, enter, exit = "heap", DOWN * 0.4, DOWN * 0.4

    def draw(self, snap, marks):
        mobs, items, size = {}, snap["items"], snap["heap_size"]
        pos = heap_positions(size)
        for i in range(size):
            iid, value = items[i]
            mobs[iid] = node(value, marks.get(iid, EDGE)).move_to(pos[i])
            if i:
                parent = items[(i - 1) // 2][0]
                mobs[("edge", parent, iid)] = link(pos[(i - 1) // 2], pos[i])
        if not size:
            mobs["empty"] = label("empty heap", 26, MUTED).move_to([0, 1, 0])
        # the array underneath: the same values, index by index
        w, gap, y = 0.78, 0.1, -2.05
        x0 = -(len(items) - 1) * (w + gap) / 2
        for i, (iid, value) in enumerate(items):
            in_heap = i < size
            colour = marks.get(iid, EDGE) if in_heap else VISITED
            mobs[("cell", iid)] = cell(value, w, 0.62, colour, 28).move_to([x0 + i * (w + gap), y, 0])
            mobs[("index", i)] = label(i, 18, MUTED).move_to([x0 + i * (w + gap), y - 0.48, 0])
        title = {"min": "min-heap: every parent is smaller than its children",
                 "max": "max-heap: every parent is larger than its children"}[snap.get("kind", "min")]
        if snap.get("kind") == "max" and not snap.get("built"):
            title = "not a heap yet"
        mobs["rule"] = label(title, 20, ACCENT if snap.get("built", True) else MUTED).move_to([0, -1.35, 0])
        return mobs

    def focus_key(self, element):
        return element

    def path(self, job, shown):
        keys = [k for k in dict.fromkeys(job["focus"]) if k in shown]
        return keys
