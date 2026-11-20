"""Every algorithm's view draws every state its simulator reaches (no video is made: fast)."""

import pytest
from dsa_explainer import algorithms
from dsa_explainer.algorithms import OpError
from dsa_explainer.media import views

ARGS = {"value": 42, "key": 11, "index": 0}


def walk(cls, preset, steps=5):
    """Snapshots before and after up to `steps` operations, trying each operation in turn."""
    ds = cls(preset)
    frames = [(ds.snapshot(), [])]
    for _ in range(steps):
        for op, needs in cls.OPS.items():
            try:
                focus = ds.run(op, {a: ARGS[a] for a in needs})
            except OpError:
                continue
            frames.append((ds.snapshot(), focus))
            break
        else:
            break
    return frames


@pytest.mark.parametrize("cls", algorithms.ALL, ids=lambda c: c.NAME)
def test_view_draws_every_state(cls):
    view = views.get(cls.VIEW)
    frames = walk(cls, next(iter(cls.PRESETS.values())), steps=4)  # one preset: drawing text is slow
    assert len(frames) >= 2, "no operation could run on the preset"
    before = view.draw(frames[0][0], {})
    for snap, focus in frames[1:]:
        job = {"focus": focus}
        after = view.draw(snap, view.marks(job, set(before)))
        assert after, "an empty picture"
        for key in view.path(job, before):  # everything pulsed before the change must be on screen
            assert key in before
        before = after
