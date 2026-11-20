"""Animation renderer (Manim). Draws one scene of a lesson as a video clip.

The language model never draws: every picture is built from the verifier's
snapshots of the real data structure. A drawer turns a snapshot into
{key: shape}. To animate a step, `morph` moves shapes whose key exists in
both the before and after picture, fades out keys that disappeared and fades
in new ones, so the same code animates a push, a dequeue, a list insert, a
tree delete or a BFS step.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import textwrap
from pathlib import Path

import manimpango
import numpy as np
from manim import (
    BOLD, DOWN, LEFT, ORIGIN, RIGHT, UP, Arrow, Circle, FadeIn, FadeOut, Indicate, LaggedStart, Line,
    RoundedRectangle, Scene, Text, Transform, VGroup, Write, linear, tempconfig,
)

from .. import config
from ..core.structures import DISPLAY_NAMES, natural_key
from .voice import silence

RENDER_VERSION = "3"  # change to re-render every cached clip after editing this file
QUALITY = {"draft": (854, 480, 15), "standard": (1280, 720, 30)}
THINK_SECONDS = 3.0  # quiz: time to think before the answer is shown

BG, FG, MUTED, CELL, EDGE = "#0f172a", "#e2e8f0", "#94a3b8", "#1e293b", "#64748b"
ACCENT, NEW, CURRENT, VISITED, QUEUED = "#38bdf8", "#4ade80", "#f472b6", "#22c55e", "#facc15"
FONT = next((f for f in ("Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans", "Liberation Sans")
             if f in manimpango.list_fonts()), "")

logging.getLogger("manim").setLevel(logging.ERROR)
logging.getLogger("av").setLevel(logging.ERROR)  # "Some options were not used" while Manim adds sound


# --- building blocks -------------------------------------------------------------


def label(text, size=28, color=FG, bold=False) -> Text:
    return Text(str(text), font=FONT, font_size=size, color=color, weight=BOLD if bold else "NORMAL")


def fit(mob, width: float):
    return mob.scale_to_fit_width(width) if mob.width > width else mob


def cell(value, w=1.0, h=0.75, stroke=EDGE, size=34) -> VGroup:
    box = RoundedRectangle(corner_radius=0.1, width=w, height=h, stroke_color=stroke, stroke_width=4,
                           fill_color=CELL, fill_opacity=1)
    return VGroup(box, fit(label(value, size), w - 0.25).move_to(box))


def node(value, stroke=EDGE, r=0.4) -> VGroup:
    ring = Circle(radius=r, stroke_color=stroke, stroke_width=4, fill_color=CELL, fill_opacity=1)
    return VGroup(ring, fit(label(value, 32), 2 * r - 0.18).move_to(ring))


def link(a, b, r=0.4, color=MUTED, arrow=False):
    """A line (or arrow) between two circle centres, stopping at their edges."""
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    d = (b - a) / np.linalg.norm(b - a)
    start, end = a + d * r, b - d * r
    if arrow:
        mob = Arrow(start, end, buff=0, stroke_width=4, color=color, max_tip_length_to_length_ratio=0.2)
    else:
        mob = Line(start, end, stroke_width=4, color=color)
    return mob.set_z_index(-1)


def pointer(name: str, target, side, buff=0.1, color=ACCENT) -> VGroup:
    """A name with an arrow pointing at target from `side` ("top", "head", ...)."""
    tip = Arrow(ORIGIN, -side * 0.55, buff=0, stroke_width=4, color=color, max_tip_length_to_length_ratio=0.4)
    return VGroup(label(name, 24, color), tip).arrange(-side, buff=0.06).next_to(target, side, buff=buff)


def option(text: str, w=6.1, h=1.0) -> VGroup:
    box = RoundedRectangle(corner_radius=0.12, width=w, height=h, stroke_color=EDGE, stroke_width=3,
                           fill_color=CELL, fill_opacity=1)
    return VGroup(box, fit(label(text, 28), w - 0.4).move_to(box))


# --- one drawer per structure: snapshot -> {key: shape} ----------------------------


def draw_stack(snap: dict, marks: dict) -> dict:
    mobs, w, h, gap, floor = {}, 2.8, 0.66, 0.1, -2.85
    for i, (iid, value) in enumerate(snap["items"]):
        mobs[iid] = cell(value, w, h, marks.get(iid, EDGE)).move_to([0, floor + 0.12 + h / 2 + i * (h + gap), 0])
    x = w / 2 + 0.18
    mobs["walls"] = VGroup(
        Line([-x, 2.75, 0], [-x, floor, 0]), Line([-x, floor, 0], [x, floor, 0]), Line([x, floor, 0], [x, 2.75, 0])
    ).set_stroke(MUTED, 4)
    if snap["items"]:
        mobs["top"] = pointer("top", mobs[snap["items"][-1][0]], LEFT, buff=0.45)
    else:
        mobs["empty"] = label("empty", 30, MUTED).move_to([0, floor + 0.5, 0])
    return mobs


def draw_queue(snap: dict, marks: dict) -> dict:
    mobs, items, w, gap = {}, snap["items"], 1.45, 0.2
    x0 = -(len(items) - 1) * (w + gap) / 2
    for i, (iid, value) in enumerate(items):
        mobs[iid] = cell(value, w, 1.1, marks.get(iid, EDGE)).move_to([x0 + i * (w + gap), 0.2, 0])
    if items:
        mobs["front"] = pointer("front", mobs[items[0][0]], DOWN)
        mobs["rear"] = pointer("rear", mobs[items[-1][0]], UP)
    else:
        mobs["empty"] = label("empty queue", 30, MUTED).move_to([0, 0.2, 0])
    return mobs


def draw_linked_list(snap: dict, marks: dict) -> dict:
    mobs, items, w, gap = {}, snap["items"], 1.1, 0.55
    x = -(len(items) * (w + gap) + 0.9) / 2 + w / 2
    prev = None
    for iid, value in items:
        box = cell(value, w, 0.95, marks.get(iid, EDGE)).move_to([x, 0.2, 0])
        mobs[iid] = box
        if prev is not None:
            mobs[("next", prev[0])] = Arrow(prev[1].get_right(), box.get_left(), buff=0.06, stroke_width=4,
                                            color=MUTED, max_tip_length_to_length_ratio=0.3)
        prev, x = (iid, box), x + w + gap
    null = label("null", 26, MUTED).move_to([x - w / 2 + 0.45, 0.2, 0])
    mobs["null"] = null
    if prev is not None:
        mobs[("next", prev[0])] = Arrow(prev[1].get_right(), null.get_left(), buff=0.06, stroke_width=4,
                                        color=MUTED, max_tip_length_to_length_ratio=0.3)
    mobs["head"] = pointer("head", mobs[items[0][0]] if items else null, UP)
    return mobs


def draw_bst(snap: dict, marks: dict) -> dict:
    mobs, nodes, root = {}, snap["nodes"], snap["root"]
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
    dx = min(1.5, 12.0 / len(order))
    dy = min(1.3, 4.9 / max(1, max(depth.values())))
    pos = {nid: np.array([(i - (len(order) - 1) / 2) * dx, 2.35 - depth[nid] * dy, 0]) for i, nid in enumerate(order)}
    for nid in order:
        value, left, right = nodes[nid]
        mobs[nid] = node(value, marks.get(nid, EDGE)).move_to(pos[nid])
        for child in (left, right):
            if child is not None:
                mobs[("edge", nid, child)] = link(pos[nid], pos[child])
    return mobs


def graph_positions(snap: dict) -> dict:
    """Rows by BFS distance from the start node, so the search reads top to bottom."""
    adj = {n: [] for n in snap["nodes"]}
    for a, b in snap["edges"]:
        adj[a].append(b)
        if not snap["directed"]:
            adj[b].append(a)
    level, order = {snap["start"]: 0}, [snap["start"]]
    for n in order:  # the list grows while we walk it: a BFS
        for m in sorted(adj[n], key=natural_key):
            if m not in level:
                level[m] = level[n] + 1
                order.append(m)
    last = max(level.values()) + 1
    order += [n for n in snap["nodes"] if n not in level]
    rows: dict[int, list] = {}
    for n in order:
        rows.setdefault(level.get(n, last), []).append(n)
    dy = min(1.5, 3.3 / max(1, len(rows) - 1))
    pos = {}
    for r, lvl in enumerate(sorted(rows)):
        row = rows[lvl]
        dx = min(3.4, 11.0 / len(row))
        for i, n in enumerate(row):
            pos[n] = np.array([(i - (len(row) - 1) / 2) * dx, 2.4 - r * dy, 0])
    return pos


def draw_graph(snap: dict, marks: dict) -> dict:
    mobs, pos = {}, graph_positions(snap)

    def colour(n):
        if n == snap["current"]:
            return CURRENT
        if n in snap["visited"]:
            return VISITED
        return QUEUED if n in snap["queue"] else EDGE

    for a, b in snap["edges"]:
        hot = marks.get(("edge", a, b)) or marks.get(("edge", b, a))
        mobs[("edge", a, b)] = link(pos[a], pos[b], color=hot or MUTED, arrow=snap["directed"])
    for n in snap["nodes"]:
        mobs[("node", n)] = node(n, colour(n)).move_to(pos[n])
    for y, name, items, col in ((-1.75, "queue", snap["queue"], QUEUED), (-2.6, "visited", snap["visited"], VISITED)):
        mobs[name] = label(name, 24, col).move_to([-5.3, y, 0])
        for i, n in enumerate(items):  # same key in both rows: a dequeued node slides down
            mobs[("token", n)] = cell(n, 0.72, 0.6, col).move_to([-4.0 + i * 0.86, y, 0])
    mobs["legend"] = VGroup(*[
        VGroup(Circle(radius=0.11, color=col, stroke_width=4), label(text, 20, MUTED)).arrange(RIGHT, buff=0.15)
        for col, text in ((CURRENT, "current"), (QUEUED, "in queue"), (VISITED, "visited"))
    ]).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([5.4, -2.2, 0])
    return mobs


DRAWERS = {"stack": draw_stack, "queue": draw_queue, "linked_list": draw_linked_list, "bst": draw_bst,
           "graph": draw_graph}
ENTER = {"stack": DOWN * 0.6, "queue": LEFT * 0.8, "linked_list": DOWN * 0.5, "bst": DOWN * 0.4, "graph": ORIGIN}
EXIT = {"stack": UP * 0.6, "queue": LEFT * 0.8, "linked_list": DOWN * 0.5, "bst": DOWN * 0.4, "graph": ORIGIN}


def focus_key(structure: str, element):
    return ("node", element) if structure == "graph" else element


def marks_for(job: dict, before_keys: set) -> dict:
    """Colours for the after picture: the path in blue, new elements in green."""
    focus = job["focus"]
    if job["structure"] == "graph":
        return {("edge", focus[0], m): ACCENT for m in focus[1:]} if focus else {}
    return {f: (ACCENT if f in before_keys else NEW) for f in focus}


# --- the scene ------------------------------------------------------------------


class LessonScene(Scene):
    def __init__(self, job: dict, **kwargs) -> None:
        self.job = job
        super().__init__(**kwargs)

    def construct(self) -> None:
        self.add_sound(self.job["audio"])
        getattr(self, "play_" + self.job["kind"])(self.job)
        self.hold_until(self.job["duration"] + 0.6)
        self.add_sound(silence())  # pads the audio track to the clip's full length

    def hold_until(self, t: float) -> None:
        if t - self.renderer.time > 0.04:
            self.wait(t - self.renderer.time)

    def header(self, job: dict) -> None:
        self.add(fit(label(job["title"], 24, MUTED), 8.0).to_corner(UP + LEFT, buff=0.35))
        if job.get("label"):
            self.add(label(job["label"], 24, ACCENT).to_corner(UP + RIGHT, buff=0.35))

    @staticmethod
    def caption(text: str):
        return fit(label(text, 28), 12.6).to_edge(DOWN, buff=0.32)

    def morph(self, shown: dict, target: dict, run_time: float, structure: str) -> dict:
        anims, result = [], {}
        for key, mob in shown.items():
            if key in target:
                anims.append(Transform(mob, target[key]))
                result[key] = mob
            else:
                anims.append(FadeOut(mob, shift=EXIT[structure]))
        for key, mob in target.items():
            if key not in shown:
                anims.append(FadeIn(mob, shift=ENTER[structure]))
                result[key] = mob
        if anims:
            self.play(*anims, run_time=run_time)
        return result

    def play_intro(self, job: dict) -> None:
        title = fit(label(job["title"], 52, bold=True), 12.5)
        sub = label(f"{DISPLAY_NAMES[job['structure']]}  |  {job['level']} level", 28, ACCENT)
        card = VGroup(title, sub).arrange(DOWN, buff=0.35)
        self.play(Write(title), FadeIn(sub, shift=UP * 0.2), run_time=1.2)
        self.wait(1.2)
        self.play(FadeOut(card, shift=UP * 0.4), run_time=0.6)
        self.header(job)
        picture = DRAWERS[job["structure"]](job["after"], {})
        self.play(*[FadeIn(m) for m in picture.values()], FadeIn(self.caption(job["caption"])), run_time=0.9)

    def play_step(self, job: dict) -> None:
        self.header(job)
        draw, structure, slow = DRAWERS[job["structure"]], job["structure"], 1 / job["speed"]
        shown = draw(job["before"], {})
        self.add(*shown.values())
        self.play(FadeIn(self.caption(job["caption"])), run_time=0.4)
        keys = [focus_key(structure, f) for f in job["focus"]]
        # 1. walk the path the operation takes (comparisons, traversal, the node leaving the queue)
        path = [("token", job["focus"][0])] if structure == "graph" and keys else [k for k in keys if k in shown]
        for key in path:
            self.play(Indicate(shown[key], color=ACCENT, scale_factor=1.15), run_time=min(0.6, 3.0 / len(path)) * slow)
        # 2. morph into the true state after the operation
        before_keys = set(shown)
        shown = self.morph(shown, draw(job["after"], marks_for(job, before_keys)), 1.2 * slow, structure)
        # 3. pulse what is new
        new = [shown[k] for k in keys if k in shown and k not in before_keys]
        if new:
            self.play(*[Indicate(m, color=NEW, scale_factor=1.12) for m in new], run_time=0.6 * slow)
        self.hold_until(job["duration"] + 0.2 + (slow - 1) * 1.5)
        # 4. back to plain colours, so the next clip starts from the same picture
        self.morph(shown, draw(job["after"], {}), 0.3, structure)

    def play_summary(self, job: dict) -> None:
        self.header(job)
        heading = label("Summary", 40, ACCENT, bold=True).move_to(UP * 2.35)
        points = job["points"] or [job["caption"]]
        rows = VGroup(*[fit(label("•  " + p, 30), 12.0) for p in points[:5]])
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.42).next_to(heading, DOWN, buff=0.6)
        self.play(FadeIn(heading), run_time=0.5)
        gap = max(0.0, job["duration"] * 0.7 / len(rows) - 0.6)
        for row in rows:
            self.play(FadeIn(row, shift=RIGHT * 0.3), run_time=0.6)
            self.wait(gap)

    def play_quiz(self, job: dict) -> None:
        self.header(job)
        question = fit(label(textwrap.fill(job["question"], 50), 30), 12.4).move_to(UP * 1.9)
        options = VGroup(*[option(f"{letter}.  {text}") for letter, text in zip("ABCD", job["options"])])
        options.arrange_in_grid(rows=2, cols=2, buff=(0.4, 0.35)).next_to(question, DOWN, buff=0.55)
        self.play(FadeIn(question), LaggedStart(*[FadeIn(o, shift=UP * 0.2) for o in options], lag_ratio=0.25),
                  run_time=1.4)
        self.hold_until(job["duration"] + 0.3)
        bar = Line(LEFT * 3, RIGHT * 3, stroke_width=10, color=ACCENT).to_edge(DOWN, buff=0.6)
        self.add(bar)
        self.play(bar.animate.scale(0.01), run_time=THINK_SECONDS, rate_func=linear)
        self.remove(bar)
        reveal = self.renderer.time
        self.add_sound(job["answer_audio"])
        right = options[job["answer"]]
        others = [o for i, o in enumerate(options) if i != job["answer"]]
        self.play(right[0].animate.set_stroke(VISITED, width=6).set_fill(VISITED, opacity=0.3),
                  *[o.animate.set_opacity(0.3) for o in others], run_time=0.6)
        self.hold_until(reveal + job["answer_duration"] + 0.6)


def render_clip(job: dict, out: Path, quality: str = "draft") -> Path:
    """Render one scene to `out` (mp4 with its narration)."""
    width, height, fps = QUALITY[quality]
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=config.CACHE_DIR, ignore_cleanup_errors=True) as tmp:
        settings = {"media_dir": tmp, "pixel_width": width, "pixel_height": height, "frame_rate": fps,
                    "background_color": BG, "disable_caching": True, "progress_bar": "none",
                    "verbosity": "ERROR", "output_file": "clip"}
        with tempconfig(settings):
            scene = LessonScene(job)
            scene.render()
            produced = scene.renderer.file_writer.movie_file_path
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(produced), str(out))
    return out
