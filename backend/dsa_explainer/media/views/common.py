"""Palette and building blocks shared by every view, and the View base class.

A view turns a simulator snapshot into {key: shape}. Keys are stable across
steps (an element keeps its key while it moves), so the generic morph in
render.py animates any operation by moving shapes whose key exists before and
after, fading out keys that disappeared and fading in new ones.

The palette is the light theme of docs/design/design-system.md: a white stage,
charcoal and gray type, leaf green for what is new or done, helpful blue for
the path an operation takes. The type is Nunito, bundled with the package
(media/fonts, SIL Open Font License) so every machine draws the same letters.
"""

from __future__ import annotations

from pathlib import Path

import manimpango
import numpy as np
from manim import BOLD, DOWN, LEFT, ORIGIN, RIGHT, UP, Arrow, Circle, Line, RoundedRectangle, Text, VGroup

# --- palette (design tokens) ---
BG = "#ffffff"  # white stage
FG = "#4b4b4b"  # friendly charcoal: values and headings
MUTED = "#777777"  # support gray: labels, indices
LINE = "#afafaf"  # utility gray: links, arrows, walls
CELL = "#ffffff"  # cell fill
EDGE = "#d4d4d4"  # a cell's resting outline (the design's soft edge, one step darker to read on video)
WASH = "#f7f7f7"  # quiet panels
ACCENT = "#1cb0f6"  # helpful blue: the path an operation walks
NEW = "#58cc02"  # leaf green: what the step added
CURRENT = "#ff9600"  # orange: the element being worked on
VISITED = "#46a302"  # deeper green: done, settled, in place
QUEUED = "#ffc800"  # yellow: waiting (queue, stack, ready set)
DONE_FILL = "#d7ffb8"  # pale leaf: the fill of values in their final place
SKY = "#ddf4ff"  # air blue: the highlighted pseudocode line
SKY_INK = "#042c60"  # deep blue lettering on the sky highlight

FONT_FILE = Path(__file__).resolve().parents[1] / "fonts" / "Nunito[wght].ttf"
if FONT_FILE.exists():
    manimpango.register_font(str(FONT_FILE))
FONT = next((f for f in ("Nunito", "Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans", "Liberation Sans")
             if f in manimpango.list_fonts()), "")

__all__ = ["ACCENT", "BG", "CELL", "CURRENT", "DONE_FILL", "DOWN", "EDGE", "FG", "FONT", "LEFT", "LINE", "MUTED",
           "NEW", "ORIGIN", "QUEUED", "RIGHT", "SKY", "SKY_INK", "UP", "VISITED", "WASH", "View", "cell", "fit",
           "label", "link", "node", "option", "pointer"]


make_text = Text  # every label goes through here; the layout tests swap in a fast stand-in


def label(text, size=28, color=FG, bold=False) -> Text:
    return make_text(str(text), font=FONT, font_size=size, color=color, weight=BOLD if bold else "NORMAL")


def fit(mob, width: float):
    return mob.scale_to_fit_width(width) if mob.width > width else mob


def cell(value, w=1.0, h=0.75, stroke=EDGE, size=34, fill=CELL) -> VGroup:
    box = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=stroke, stroke_width=4,
                           fill_color=fill, fill_opacity=1)
    return VGroup(box, fit(label(value, size, bold=True), w - 0.25).move_to(box))


def node(value, stroke=EDGE, r=0.4) -> VGroup:
    ring = Circle(radius=r, stroke_color=stroke, stroke_width=4, fill_color=CELL, fill_opacity=1)
    return VGroup(ring, fit(label(value, 32, bold=True), 2 * r - 0.18).move_to(ring))


def link(a, b, r=0.4, color=LINE, arrow=False):
    """A line (or arrow) between two circle centres, stopping at their edges."""
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    d = (b - a) / np.linalg.norm(b - a)
    start, end = a + d * r, b - d * r
    if arrow:
        mob = Arrow(start, end, buff=0, stroke_width=4, color=color, max_tip_length_to_length_ratio=0.2)
    else:
        mob = Line(start, end, stroke_width=4, color=color)
    return mob.set_z_index(-1)


def pointer(name: str, target, side, buff=0.1, color=ACCENT, size=24) -> VGroup:
    """A name with an arrow pointing at target from `side` ("top", "head", ...)."""
    tip = Arrow(ORIGIN, -side * 0.55, buff=0, stroke_width=4, color=color, max_tip_length_to_length_ratio=0.4)
    return VGroup(label(name, size, color, bold=True), tip).arrange(-side, buff=0.06).next_to(target, side, buff=buff)


def option(text: str, w=6.1, h=1.0) -> VGroup:
    box = RoundedRectangle(corner_radius=0.16, width=w, height=h, stroke_color=EDGE, stroke_width=4,
                           fill_color=CELL, fill_opacity=1)
    return VGroup(box, fit(label(text, 28), w - 0.4).move_to(box))


class View:
    """How one family of snapshots is drawn and animated. Subclasses override draw()."""

    name = ""
    enter = ORIGIN  # direction new shapes slide in from
    exit = ORIGIN  # direction removed shapes slide out to
    arc = 0.0  # opt-in: elements that move travel on an arc of this angle, so values that swap pass each other

    def draw(self, snap: dict, marks: dict) -> dict:
        raise NotImplementedError

    def focus_key(self, element):
        """The shape key of one element the simulator reported (its run() return value)."""
        return tuple(element) if isinstance(element, list) else element

    def marks(self, job: dict, before_keys: set) -> dict:
        """Colours for the after picture: the path in blue, new elements in green."""
        keys = [self.focus_key(f) for f in job["focus"]]
        return {k: (ACCENT if k in before_keys else NEW) for k in keys}

    def path(self, job: dict, shown: dict) -> list:
        """Shapes to pulse, in order, before the picture changes (comparisons, the walk to a position)."""
        keys = [self.focus_key(f) for f in job["focus"]]
        return list(dict.fromkeys(k for k in keys if k in shown))

    def arc_for(self, key) -> float:
        """The arc a moving shape takes: elements (integer keys) arc, labels and pointers slide straight."""
        return self.arc if isinstance(key, int) else 0.0
