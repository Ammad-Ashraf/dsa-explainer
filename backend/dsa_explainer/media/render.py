"""Animation renderer (Manim). Draws one scene of a lesson as a video clip.

The language model never draws: every picture is built from the verifier's
snapshots of the real simulation. The algorithm's view (media/views) turns a
snapshot into {key: shape}. To animate a step, `morph` moves shapes whose key
exists in both the before and after picture, fades out keys that disappeared
and fades in new ones, so the same code animates a push, a dequeue, a swap, a
heap sift, a tree delete or a graph step. Views that opt in (View.arc) move
elements on an arc, so two values that swap pass each other.

Beside the structure, a step shows its pseudocode with the lines the operation
ran highlighted and a strip of the simulator's facts after the step (see
panels.py); both were recorded by the verifier, never written by the model.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import textwrap
from pathlib import Path

import numpy as np
from manim import (
    DOWN, LEFT, RIGHT, UP, FadeIn, FadeOut, Indicate, LaggedStart, Line, Scene, Transform, VGroup,
    Write, linear, tempconfig,
)

from .. import config
from . import panels, views
from .views.common import ACCENT, BG, CELL, EDGE, FG, MUTED, NEW, VISITED, fit, label, option
from .voices import silence

RENDER_VERSION = "5"  # change to re-render every cached clip after editing the renderer or a view
QUALITY = {"draft": (854, 480, 15), "standard": (1280, 720, 30), "high": (1920, 1080, 30)}
THINK_SECONDS = 3.0  # quiz: time to think before the answer is shown
QUIZ_INTRO_SECONDS = 1.4  # quiz: the question and options appearing

__all__ = ["ACCENT", "BG", "CELL", "EDGE", "FG", "MUTED", "LessonScene", "QUALITY", "RENDER_VERSION", "label",
           "render_clip"]

logging.getLogger("manim").setLevel(logging.ERROR)
logging.getLogger("av").setLevel(logging.ERROR)  # "Some options were not used" while Manim adds sound


class LessonScene(Scene):
    def __init__(self, job: dict, **kwargs) -> None:
        self.job = job
        self.view = views.get(job["view"])
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

    def picture(self, snap: dict, marks: dict) -> dict:
        """The view's drawing of a snapshot, placed left of the pseudocode card when the clip has one."""
        picture = self.view.draw(snap, marks)
        return panels.place(picture) if self.job.get("code") else picture

    def morph_anims(self, shown: dict, target: dict, arcs: bool = True) -> tuple[list, dict]:
        """Transforms for shapes in both pictures (on the view's arc when they move), fades for the rest."""
        anims, result = [], {}
        for key, mob in shown.items():
            if key in target:
                moved = np.linalg.norm(target[key].get_center() - mob.get_center()) > 0.05
                arc = self.view.arc_for(key) if arcs and moved else 0.0
                anims.append(Transform(mob, target[key], path_arc=arc))
                result[key] = mob
            else:
                anims.append(FadeOut(mob, shift=self.view.exit))
        for key, mob in target.items():
            if key not in shown:
                anims.append(FadeIn(mob, shift=self.view.enter))
                result[key] = mob
        return anims, result

    def morph(self, shown: dict, target: dict, run_time: float, arcs: bool = True) -> dict:
        anims, result = self.morph_anims(shown, target, arcs)
        if anims:
            self.play(*anims, run_time=run_time)
        return result

    def code(self, job: dict) -> dict:
        """Add the pseudocode card; returns its rows by line index."""
        if not job.get("code"):
            return {}
        card, rows = panels.code_card(job["code"])
        self.add(card, *rows.values())
        return rows

    def light_up(self, rows: dict, lines: list) -> list:
        """Animations that highlight the pseudocode lines the step's operation ran."""
        anims = []
        for i in lines:
            if i in rows:
                anims += [FadeIn(panels.highlight(rows[i])), rows[i].animate.set_color(panels.line_colour(True))]
        return anims

    def play_intro(self, job: dict) -> None:
        title = fit(label(job["title"], 52, bold=True), 12.5)
        sub = label(f"{job['structure_title']}  |  {job['level']} level", 28, ACCENT)
        card = VGroup(title, sub).arrange(DOWN, buff=0.35)
        self.play(Write(title), FadeIn(sub, shift=UP * 0.2), run_time=1.2)
        self.wait(1.2)
        self.play(FadeOut(card, shift=UP * 0.4), run_time=0.6)
        self.header(job)
        rows = self.code(job)
        self.remove(*rows.values())  # the card stays; the rows fade in with the picture
        extras = list(rows.values()) + list(panels.strip(job.get("strip_after", [])).values())
        picture = self.picture(job["after"], {})
        self.play(*[FadeIn(m) for m in list(picture.values()) + extras], FadeIn(self.caption(job["caption"])),
                  run_time=0.9)

    def play_step(self, job: dict) -> None:
        self.header(job)
        view, slow = self.view, 1 / job["speed"]
        rows = self.code(job)
        facts = panels.strip(job.get("strip_before", []))
        self.add(*facts.values())
        shown = self.picture(job["before"], {})
        self.add(*shown.values())
        # 1. the caption, and the pseudocode lines this operation runs
        self.play(FadeIn(self.caption(job["caption"])), *self.light_up(rows, job.get("lines", [])), run_time=0.5)
        # 2. walk the path the operation takes (comparisons, traversal, the node leaving the queue)
        path = view.path(job, shown)
        for key in path:
            self.play(Indicate(shown[key], color=ACCENT, scale_factor=1.15), run_time=min(0.6, 3.0 / len(path)) * slow)
        # 3. morph into the true state after the operation; the facts strip updates with it, changes in blue
        before_keys = set(shown)
        moves, shown = self.morph_anims(shown, self.picture(job["after"], view.marks(job, before_keys)))
        changed = panels.changed_facts(job.get("strip_before", []), job.get("strip_after", []))
        fact_moves, facts = self.morph_anims(facts, panels.strip(job.get("strip_after", []), changed), arcs=False)
        if moves or fact_moves:
            self.play(*moves, *fact_moves, run_time=1.2 * slow)
        # 4. pulse what is new
        keys = [view.focus_key(f) for f in job["focus"]]
        new = [shown[k] for k in dict.fromkeys(keys) if k in shown and k not in before_keys]
        if new:
            self.play(*[Indicate(m, color=NEW, scale_factor=1.12) for m in new], run_time=0.6 * slow)
        self.hold_until(job["duration"] + 0.2 + (slow - 1) * 1.5)
        # 5. back to plain colours, so the next clip starts from the same picture
        self.morph(shown, self.picture(job["after"], {}), 0.3, arcs=False)

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
                  run_time=QUIZ_INTRO_SECONDS)
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


def compose(job: dict, when: str = "after") -> dict:
    """Every shape of a scene's resting picture ({key: mobject}) as its clip shows it after (or before) the
    operation: the placed structure, the pseudocode card and rows, and the facts strip. For the layout tests."""
    view = views.get(job["view"])
    picture = view.draw(job[when], {})
    out = {("picture", k): m for k, m in (panels.place(picture) if job.get("code") else picture).items()}
    if job.get("code"):
        card, rows = panels.code_card(job["code"])
        out[("code", "card")] = card
        out.update({("code", i): r for i, r in rows.items()})
    out.update(panels.strip(job.get("strip_" + when, [])))
    return out


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
