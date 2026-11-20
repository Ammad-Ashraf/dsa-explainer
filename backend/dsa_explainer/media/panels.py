"""What a step's video shows beside the structure: the pseudocode card and the facts strip.

Neither comes from the language model. The verifier records, for every scene,
the pseudocode lines the simulator's operation ran (Structure.code_lines) and
the facts strip before and after it (Structure.strip), and the renderer only
lays them out:

    +-------------------------------------------+---------------+
    | title                               step  |               |
    |   [ swaps 3 ] [ comparisons 5 ] [ placed ]|  pseudocode   |
    |                                           |  > line run   |
    |          the structure (scaled)           |    ...        |
    |                                           |               |
    |                 caption                                   |
    +-----------------------------------------------------------+

Everything here is positioned in Manim's frame units (14.2 x 8).
"""

from __future__ import annotations

import textwrap

import numpy as np
from manim import DOWN, LEFT, ORIGIN, RIGHT, UP, RoundedRectangle, VGroup

from .views.common import ACCENT, EDGE, FG, MUTED, SKY, SKY_INK, WASH, fit, label

# the structure's picture is drawn for the whole frame, then scaled into the left part
PICTURE_SCALE = 0.8
PICTURE_SHIFT = np.array([-2.3, -0.5, 0.0])
# the pseudocode card fills the right column
CODE_LEFT, CODE_RIGHT, CODE_TOP, CODE_BOTTOM = 2.75, 6.75, 3.0, -2.95
CODE_WRAP = 30  # characters per row before a pseudocode line wraps
CODE_SIZE = 20
INDENT = 0.28  # frame units per level of indentation (4 spaces)
# the facts strip runs across the top of the picture
STRIP_Y, STRIP_CENTER_X, STRIP_WIDTH = 2.7, -2.3, 9.4


def place(picture: dict) -> dict:
    """Scale a view's full-frame picture into the area left of the pseudocode card."""
    for mob in picture.values():
        mob.scale(PICTURE_SCALE, about_point=ORIGIN).shift(PICTURE_SHIFT)
    return picture


def code_card(code: list[str]) -> tuple[RoundedRectangle, dict]:
    """The card and one row group per pseudocode line ({line index: VGroup of wrapped rows})."""
    width, height = CODE_RIGHT - CODE_LEFT, CODE_TOP - CODE_BOTTOM
    card = RoundedRectangle(corner_radius=0.18, width=width, height=height, stroke_color=EDGE, stroke_width=3,
                            fill_color=WASH, fill_opacity=1)
    card.move_to([(CODE_LEFT + CODE_RIGHT) / 2, (CODE_TOP + CODE_BOTTOM) / 2, 0]).set_z_index(-2)  # under highlights
    title = label("PSEUDOCODE", 16, MUTED, bold=True)
    title.move_to(card.get_corner(UP + LEFT) + np.array([0.3 + title.width / 2, -0.32, 0]))
    lines = {}
    for i, line in enumerate(code):
        level = (len(line) - len(line.lstrip(" "))) // 4
        rows = textwrap.wrap(line.strip(), CODE_WRAP - 3 * level, subsequent_indent="  ")
        group = VGroup(*[label(row, CODE_SIZE, MUTED) for row in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        group.indent = level  # remembered for alignment after scaling
        lines[i] = group
    body = VGroup(*lines.values()).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
    for group in lines.values():
        group.shift(RIGHT * INDENT * group.indent)
    room_w, room_h = width - 0.55, height - 0.95
    if body.width > room_w or body.height > room_h:
        body.scale(min(room_w / body.width, room_h / body.height))
    body.next_to(title, DOWN, buff=0.28, aligned_edge=LEFT)
    return VGroup(card, title), lines


def highlight(rows: VGroup) -> RoundedRectangle:
    """The air-blue bar behind one pseudocode line."""
    width = CODE_RIGHT - CODE_LEFT - 0.3
    bar = RoundedRectangle(corner_radius=0.1, width=width, height=rows.height + 0.16, stroke_width=0,
                           fill_color=SKY, fill_opacity=1)
    return bar.move_to([(CODE_LEFT + CODE_RIGHT) / 2, rows.get_center()[1], 0]).set_z_index(-1)


def line_colour(lit: bool) -> str:
    return SKY_INK if lit else MUTED


def strip(facts: list, changed: set | None = None) -> dict:
    """The facts strip as {("fact", label): chip}; facts whose value changed are blue."""
    if not facts:
        return {}
    chips = {}
    for name, value in facts:
        hot = changed is not None and name in changed
        text = VGroup(label(name, 16, MUTED, bold=True), label(value, 24, ACCENT if hot else FG, bold=True))
        text.arrange(DOWN, buff=0.08)
        fit(text[1], 3.6)
        box = RoundedRectangle(corner_radius=0.14, width=max(1.0, text.width + 0.4), height=text.height + 0.26,
                               stroke_color=ACCENT if hot else EDGE, stroke_width=3, fill_color="#ffffff",
                               fill_opacity=1)
        chips[("fact", name)] = VGroup(box, text.move_to(box))
    row = VGroup(*chips.values()).arrange(RIGHT, buff=0.18)
    fit(row, STRIP_WIDTH)
    row.move_to([STRIP_CENTER_X, STRIP_Y, 0])
    return chips


def changed_facts(before: list, after: list) -> set:
    old = {name: value for name, value in before}
    return {name for name, value in after if old.get(name) != value}
