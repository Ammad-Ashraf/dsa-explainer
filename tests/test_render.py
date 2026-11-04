"""Renders one real clip (voice + animation). Takes about 10 seconds."""

import pytest

from dsa_explainer import config, render, video, voice
from dsa_explainer.verifier import verify_lesson

from .helpers import load

pytestmark = pytest.mark.skipif(not config.KOKORO_MODEL.exists(), reason="voice model not downloaded")


@pytest.mark.parametrize("name", ["stack", "bfs"])
def test_one_step_clip_renders_with_sound(tmp_path, name):
    lesson = load(name)
    job = video.jobs_for(lesson, verify_lesson(lesson))[1]  # the first step
    job["audio"], job["duration"] = voice.speak("A short test sentence.")
    out = render.render_clip(job, tmp_path / "clip.mp4")
    assert video.clip_seconds(out) >= job["duration"]
