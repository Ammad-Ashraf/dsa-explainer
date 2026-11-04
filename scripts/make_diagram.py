"""Draws the system architecture diagram, docs/architecture.png, with Manim.

    python scripts/make_diagram.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
from manim import DOWN, LEFT, RIGHT, UP, Arrow, CurvedArrow, RoundedRectangle, Scene, VGroup, tempconfig  # noqa: E402

from dsa_explainer.render import ACCENT, BG, CELL, FG, MUTED, label  # noqa: E402

API, LOCAL, PERSON = "#60a5fa", "#4ade80", "#e2e8f0"
W, H = 2.75, 1.2


def box(title: str, sub: str, colour: str, at) -> VGroup:
    rect = RoundedRectangle(corner_radius=0.14, width=W, height=H, stroke_color=colour, stroke_width=5,
                            fill_color=CELL, fill_opacity=1).move_to(np.array([*at, 0]))
    text = VGroup(label(title, 25, FG, bold=True), label(sub, 18, MUTED)).arrange(DOWN, buff=0.12)
    if text.width > W - 0.3:
        text.scale_to_fit_width(W - 0.3)
    return VGroup(rect, text.move_to(rect))


def link(a: VGroup, b: VGroup, text: str = "", side=UP, colour=MUTED, start=None, end=None) -> VGroup:
    arrow = Arrow(start if start is not None else a.get_center(), end if end is not None else b.get_center(),
                  buff=0.0, stroke_width=4, color=colour, max_tip_length_to_length_ratio=0.12)
    if start is None:  # trim to the box edges
        arrow.put_start_and_end_on(*_edges(a, b))
    parts = VGroup(arrow)
    if text:
        parts.add(label(text, 17, MUTED).next_to(arrow.get_center(), side, buff=0.22))
    return parts


def _edges(a: VGroup, b: VGroup):
    ca, cb = a.get_center(), b.get_center()
    d = cb - ca
    if abs(d[0]) * H > abs(d[1]) * W:  # leaves through a side
        sa, sb = (a.get_right(), b.get_left()) if d[0] > 0 else (a.get_left(), b.get_right())
    else:  # leaves through the top or bottom
        sa, sb = (a.get_top(), b.get_bottom()) if d[1] > 0 else (a.get_bottom(), b.get_top())
    return sa, sb


class Architecture(Scene):
    def construct(self) -> None:
        title = label("DSA Explainer: system architecture", 34, FG, bold=True).move_to(UP * 3.55)

        learner = box("Learner", "Gradio web app", PERSON, (-5.3, 1.75))
        planner = box("1. Lesson planner", "LLM writes a JSON scene plan", API, (-1.75, 1.75))
        verifier = box("3. Step verifier", "runs the real data structure", LOCAL, (1.75, 1.75))
        quiz = box("5. Quiz generator", "LLM writes, verifier checks", API, (5.3, 1.75))
        revision = box("6. Revision control", "rules or LLM, then re-verified", API, (-1.75, 0.0))
        voice = box("4. Voice", "Kokoro-82M on the CPU", LOCAL, (5.3, -1.75))
        renderer = box("2. Renderer", "Manim, 4 clips at once", LOCAL, (1.75, -1.75))
        cache = box("Clip cache", "keyed by what a clip shows", LOCAL, (-1.75, -1.75))
        joiner = box("ffmpeg", "joins clips into lesson.mp4", LOCAL, (-5.3, -1.75))
        verifier[0].set_stroke(ACCENT, 7)

        feedback = CurvedArrow(verifier.get_top() + LEFT * 0.6, planner.get_top() + RIGHT * 0.6, angle=np.pi / 2.2,
                               color="#f472b6", stroke_width=4)
        feedback_text = label("errors + the true state (up to 4 attempts)", 17, "#f472b6").next_to(feedback, UP, 0.08)
        arrows = VGroup(
            link(learner, planner, "topic"),
            link(planner, verifier, "plan"),
            link(verifier, quiz, "lesson"),
            link(quiz, voice, "lesson + quiz", side=RIGHT),
            link(voice, renderer, "audio"),
            link(renderer, cache, "clips"),
            link(cache, joiner),
            link(joiner, learner, "video", side=LEFT),
            link(learner, revision, start=learner.get_bottom() + RIGHT * 0.9, end=revision.get_left()),
            link(revision, verifier, start=revision.get_right(), end=verifier.get_bottom() + LEFT * 0.9),
        )
        request = label("change request", 17, MUTED).next_to(revision, LEFT, buff=0.15).shift(DOWN * 0.45)
        legend = VGroup(*[
            VGroup(RoundedRectangle(corner_radius=0.06, width=0.42, height=0.26, stroke_color=c, stroke_width=4,
                                    fill_color=CELL, fill_opacity=1), label(t, 18, MUTED)).arrange(RIGHT, buff=0.15)
            for c, t in ((API, "uses the LLM API"), (LOCAL, "runs locally"))
        ]).arrange(RIGHT, buff=0.7).move_to(DOWN * 3.45)
        self.add(arrows, feedback, feedback_text, request, learner, planner, verifier, quiz, revision, voice,
                 renderer, cache, joiner, title, legend)


def main() -> None:
    out = ROOT / "docs" / "architecture.png"
    out.parent.mkdir(exist_ok=True)
    with tempconfig({"pixel_width": 1920, "pixel_height": 1080, "background_color": BG, "disable_caching": True,
                     "verbosity": "ERROR", "progress_bar": "none"}):
        scene = Architecture()
        scene.construct()
        scene.renderer.update_frame(scene)
        scene.renderer.camera.get_image().save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
