"""Hash-table buckets with chains, and dynamic-programming tables."""

from __future__ import annotations

from manim import Arrow

from .common import ACCENT, CURRENT, EDGE, LEFT, MUTED, NEW, RIGHT, UP, View, cell, label


class BucketsView(View):
    name, enter, exit = "buckets", RIGHT * 0.6, RIGHT * 0.6

    def draw(self, snap, marks):
        mobs, buckets, active = {}, snap["buckets"], snap.get("active")
        m = len(buckets)
        dy = min(0.85, 5.0 / m)
        top = (m - 1) * dy / 2 + 0.3
        for b, chain in enumerate(buckets):
            y = top - b * dy
            colour = marks.get(("bucket", b)) or (ACCENT if b == active else EDGE)
            head = cell(b, 0.8, min(0.66, dy - 0.12), colour, 26).move_to([-4.6, y, 0])
            mobs[("bucket", b)] = head
            prev = head
            for k, (iid, key) in enumerate(chain):
                box = cell(key, 0.95, min(0.66, dy - 0.12), marks.get(iid, EDGE), 28).move_to([-3.0 + k * 1.55, y, 0])
                mobs[iid] = box
                mobs[("arrow", iid)] = Arrow(prev.get_right(), box.get_left(), buff=0.05, stroke_width=3, color=MUTED,
                                             max_tip_length_to_length_ratio=0.3)
                prev = box
        mobs["rule"] = label(f"bucket = key mod {m}", 24, ACCENT).to_corner(UP + LEFT).shift([0.3, -0.55, 0])
        return mobs


class TableView(View):
    name, enter, exit = "table", UP * 0.3, UP * 0.3

    def draw(self, snap, marks):
        mobs, cells, current = {}, snap["cells"], snap.get("current")
        n = len(cells)
        w = min(1.2, 11.5 / n)
        x0 = -(n - 1) * w / 2
        labels = snap.get("labels") or [str(i) for i in range(n)]
        for i, (iid, value) in enumerate(cells):
            text = "" if value is None else ("∞" if value == "inf" else value)
            colour = marks.get(iid) or (CURRENT if i == current else EDGE)
            mobs[iid] = cell(text, w - 0.08, 1.0, colour, 30).move_to([x0 + i * w, 0.2, 0])
            mobs[("head", i)] = label(labels[i], 20, MUTED).move_to([x0 + i * w, 1.0, 0])
        if snap.get("caption"):
            mobs["caption"] = label(snap["caption"], 26, ACCENT).move_to([0, 2.0, 0])
        if current is not None:
            mobs["arrow"] = label("just filled", 20, NEW).move_to([x0 + current * w, -0.65, 0])
        return mobs
