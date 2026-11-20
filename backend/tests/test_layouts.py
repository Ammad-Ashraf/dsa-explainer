"""Golden layouts: where every shape of every saved lesson's pictures sits.

Pixel diffs of video frames break on every font hinting or encoder change and
say nothing about what moved. Instead, for each saved plan, the resting picture
of the intro and of every step (the structure, the facts strip, and once per
plan the pseudocode card) is reduced to {shape key: centre and size}, rounded,
and compared with the approved copy in tests/golden/layouts/.

After an intended change to a view or the panels, approve the new layouts with

    DSA_UPDATE_GOLDEN=1 python -m pytest backend/tests/test_layouts.py

and review the JSON diff like any other change.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from dsa_explainer.core.verifier import verify_lesson
from dsa_explainer.media import panels, render, video

from .helpers import EXAMPLES, load

GOLDEN = Path(__file__).parent / "golden" / "layouts"


def text_box(text, font_size=28, color=None, **_):
    """A stand-in for Manim's Text with Nunito's average metrics: real text takes about a second per label
    to typeset, and its exact size differs a little between Pango builds; this is fast and the same everywhere."""
    from manim import Rectangle

    return Rectangle(width=max(0.01, 0.0062 * font_size * len(text)), height=0.01 * font_size, stroke_width=0,
                     fill_color=color or "#000000", fill_opacity=1)


@pytest.fixture(autouse=True)
def fast_text(monkeypatch):
    from dsa_explainer.media.views import common

    monkeypatch.setattr(common, "make_text", text_box)
UPDATE = os.getenv("DSA_UPDATE_GOLDEN") == "1"
TOLERANCE = 0.05  # frame units (the frame is 14.2 wide): small enough to catch any real move


def shape(mob) -> list[float]:
    x, y, _ = mob.get_center()
    return [round(float(x), 3), round(float(y), 3), round(float(mob.width), 3), round(float(mob.height), 3)]


def shapes(mobs: dict) -> dict:
    return {repr(key): shape(mob) for key, mob in sorted(mobs.items(), key=lambda kv: repr(kv[0]))}


def layout(name: str) -> dict:
    lesson = load(name)
    jobs = [j for j in video.jobs_for(lesson, verify_lesson(lesson)) if j["kind"] in ("intro", "step")]
    card, rows = panels.code_card(jobs[0]["code"])
    scenes = []
    for job in jobs:
        mobs = render.compose(job, "after")
        scenes.append({"name": job["name"], "lines": job.get("lines", []),
                       "shapes": shapes({k: m for k, m in mobs.items() if k[0] != "code"})})
    return {"structure": lesson.structure, "code": shapes({"card": card, **{f"line {i}": r for i, r in rows.items()}}),
            "scenes": scenes}


def differences(old: dict, new: dict, where: str) -> list[str]:
    problems = []
    for key in sorted(set(old) | set(new)):
        if key not in new:
            problems.append(f"{where}: {key} is no longer drawn")
        elif key not in old:
            problems.append(f"{where}: {key} is new")
        elif any(abs(a - b) > TOLERANCE for a, b in zip(old[key], new[key])):
            problems.append(f"{where}: {key} moved from {old[key]} to {new[key]}")
    return problems


@pytest.mark.parametrize("name", EXAMPLES)
def test_layout_matches_the_approved_one(name):
    path = GOLDEN / f"{name}.json"
    current = layout(name)
    if UPDATE or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(current, indent=1) + "\n", encoding="utf-8")
        if not UPDATE:
            pytest.fail(f"no approved layout for {name} yet: wrote {path.name}; review it and run again")
        return
    approved = json.loads(path.read_text(encoding="utf-8"))
    problems = differences(approved["code"], current["code"], "pseudocode")
    if [s["name"] for s in approved["scenes"]] != [s["name"] for s in current["scenes"]]:
        problems.append("the scenes changed: " + ", ".join(s["name"] for s in current["scenes"]))
    for old, new in zip(approved["scenes"], current["scenes"]):
        if old["lines"] != new["lines"]:
            problems.append(f"{new['name']}: highlights pseudocode lines {new['lines']}, not {old['lines']}")
        problems += differences(old["shapes"], new["shapes"], new["name"])
    assert not problems, (f"{len(problems)} layout change(s) in {name} (approve with DSA_UPDATE_GOLDEN=1):\n"
                          + "\n".join(problems[:25]))


def test_pictures_stay_clear_of_the_pseudocode_card_and_the_caption(fast_text):
    """A layout rule the golden files cannot express: nothing of the structure spills under the card or the caption."""
    for name in EXAMPLES:
        path = GOLDEN / f"{name}.json"
        if not path.exists():
            continue
        for scene in json.loads(path.read_text(encoding="utf-8"))["scenes"]:
            for key, (x, y, w, h) in scene["shapes"].items():
                if key.startswith("('picture'"):
                    assert x + w / 2 <= panels.CODE_LEFT + 0.05, f"{name} {scene['name']}: {key} runs under the card"
                    assert y - h / 2 >= -3.15, f"{name} {scene['name']}: {key} runs into the caption"
                    assert x - w / 2 >= -7.1, f"{name} {scene['name']}: {key} leaves the frame"
