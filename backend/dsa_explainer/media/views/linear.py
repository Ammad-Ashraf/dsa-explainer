"""Stack, queue (and deque) and linked list pictures."""

from __future__ import annotations

from manim import Arrow, Line, VGroup

from .common import DOWN, EDGE, LEFT, LINE, MUTED, UP, View, cell, label, pointer


class StackView(View):
    name, enter, exit = "stack", DOWN * 0.6, UP * 0.6

    def draw(self, snap, marks):
        mobs, w, h, gap, floor = {}, 2.8, 0.66, 0.1, -2.85
        for i, (iid, value) in enumerate(snap["items"]):
            mobs[iid] = cell(value, w, h, marks.get(iid, EDGE)).move_to([0, floor + 0.12 + h / 2 + i * (h + gap), 0])
        x = w / 2 + 0.18
        mobs["walls"] = VGroup(
            Line([-x, 2.75, 0], [-x, floor, 0]), Line([-x, floor, 0], [x, floor, 0]),
            Line([x, floor, 0], [x, 2.75, 0])
        ).set_stroke(LINE, 4)
        if snap["items"]:
            mobs["top"] = pointer("top", mobs[snap["items"][-1][0]], LEFT, buff=0.45)
        else:
            mobs["empty"] = label("empty", 30, MUTED).move_to([0, floor + 0.5, 0])
        return mobs


class QueueView(View):
    name, enter, exit = "queue", LEFT * 0.8, LEFT * 0.8

    def draw(self, snap, marks):
        mobs, items, w, gap = {}, snap["items"], 1.45, 0.2
        x0 = -(len(items) - 1) * (w + gap) / 2
        for i, (iid, value) in enumerate(items):
            mobs[iid] = cell(value, w, 1.1, marks.get(iid, EDGE)).move_to([x0 + i * (w + gap), 0.2, 0])
        if items:
            mobs["front"] = pointer("front", mobs[items[0][0]], DOWN)
            mobs["rear"] = pointer("rear", mobs[items[-1][0]], UP)
        else:
            mobs["empty"] = label("empty", 30, MUTED).move_to([0, 0.2, 0])
        return mobs


class LinkedListView(View):
    name, enter, exit = "linked_list", DOWN * 0.5, DOWN * 0.5

    def draw(self, snap, marks):
        mobs, items, w, gap = {}, snap["items"], 1.1, 0.55
        x = -(len(items) * (w + gap) + 0.9) / 2 + w / 2
        prev = None
        for iid, value in items:
            box = cell(value, w, 0.95, marks.get(iid, EDGE)).move_to([x, 0.2, 0])
            mobs[iid] = box
            if prev is not None:
                mobs[("next", prev[0])] = Arrow(prev[1].get_right(), box.get_left(), buff=0.06, stroke_width=4,
                                                color=LINE, max_tip_length_to_length_ratio=0.3)
            prev, x = (iid, box), x + w + gap
        null = label("null", 26, MUTED).move_to([x - w / 2 + 0.45, 0.2, 0])
        mobs["null"] = null
        if prev is not None:
            mobs[("next", prev[0])] = Arrow(prev[1].get_right(), null.get_left(), buff=0.06, stroke_width=4,
                                            color=LINE, max_tip_length_to_length_ratio=0.3)
        mobs["head"] = pointer("head", mobs[items[0][0]] if items else null, UP)
        return mobs
