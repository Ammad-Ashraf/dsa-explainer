"""Arrays: bars for sorting (height = value) and indexed cells for searching.

Each value keeps its key while it moves, so swaps, shifts and merges animate
as values travelling to their new index, on an arc (View.arc) so two values
that swap visibly pass each other. Pointers (i, low, mid, high, pivot), the
active range, the sorted region and faded (eliminated) cells come from the
simulator's snapshot.
"""

from __future__ import annotations

from manim import PI, Line, RoundedRectangle, VGroup

from .common import (
    ACCENT, CELL, CURRENT, DONE_FILL, DOWN, EDGE, FG, MUTED, NEW, UP, VISITED, View, cell, fit, label, pointer,
)

POINTER_COLOURS = {"mid": CURRENT, "pivot": CURRENT, "i": ACCENT, "low": ACCENT, "high": ACCENT}


class ArrayView(View):
    name, enter, exit = "array", DOWN * 0.4, DOWN * 0.4
    arc = -PI * 0.6  # swapped values pass each other, one over and one under

    def draw(self, snap, marks):
        mobs, items = {}, snap["items"]
        n = len(items)
        bars = snap.get("style", "bars") == "bars"
        w = min(1.25, 11.0 / max(n, 1))
        gap = w * 0.16
        x0 = -(n - 1) * (w + gap) / 2
        xs = [x0 + i * (w + gap) for i in range(n)]
        sorted_ix, faded = set(snap.get("sorted") or []), set(snap.get("faded") or [])
        found = snap.get("found")
        values = [v for _, v in items]
        low, high = min(values + [0]), max(values + [1])
        base = -1.55
        for i, (iid, value) in enumerate(items):
            stroke = marks.get(iid) or (VISITED if i in sorted_ix or i == found else EDGE)
            if bars:
                h = 0.45 + 3.3 * (value - low) / ((high - low) or 1)
                fill = DONE_FILL if i in sorted_ix else CELL
                bar = RoundedRectangle(corner_radius=0.08, width=w, height=h, stroke_color=stroke, stroke_width=4,
                                       fill_color=fill, fill_opacity=1).move_to([xs[i], base + h / 2, 0])
                text = fit(label(value, 28, FG, bold=True), w - 0.1).next_to(bar, UP, buff=0.08)
                shape = VGroup(bar, text)
            else:
                shape = cell(value, w, 0.95, stroke, 32).move_to([xs[i], 0.3, 0])
            if i in faded:
                shape.set_opacity(0.3)
            mobs[iid] = shape
        y_index = base - 0.3 if bars else -0.45
        for i in range(n):
            mobs[("index", i)] = label(i, 20, MUTED).move_to([xs[i], y_index, 0])
        if snap.get("range"):
            lo, hi = snap["range"]
            y = y_index - 0.32
            mobs["range"] = Line([xs[lo] - w / 2, y, 0], [xs[hi] + w / 2, y, 0], stroke_width=6, color=ACCENT)
        stacked: dict[int, int] = {}  # pointers on the same index stack downwards
        for name, index in sorted((snap.get("pointers") or {}).items(), key=lambda p: (p[1], p[0])):
            if index is not None and 0 <= index < n:
                below = stacked.get(index, 0)
                stacked[index] = below + 1
                mobs[("pointer", name)] = pointer(name, mobs[("index", index)], DOWN, buff=0.4 + 0.95 * below,
                                                  color=POINTER_COLOURS.get(name, ACCENT), size=22)
        if "target" in snap:
            mobs["target"] = label(f"target {snap['target']}", 26, CURRENT).to_corner(UP).shift(DOWN * 0.55)
        if found is not None:
            mobs["found"] = label("found", 24, NEW).next_to(mobs[items[found][0]], UP, buff=0.12)
        if sorted_ix and bars:
            mobs["sorted-label"] = label("in place", 20, VISITED).move_to([xs[max(sorted_ix)], base - 0.95, 0])
        return mobs

    def path(self, job, shown):
        keys = [k for k in dict.fromkeys(job["focus"]) if k in shown]
        return keys[:6]
