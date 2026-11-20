"""Mutation testing: plant one mistake in every saved plan, many ways, and require the verifier to catch it.

The full table is printed by scripts/mutation_report.py and recorded in
docs/research/verification.md. These thresholds only move up.
"""

from collections import defaultdict

import pytest
from dsa_explainer.core import mutants

from .helpers import EXAMPLES, load

ALWAYS_CAUGHT = ("wrong claimed_state", "wrong quiz answer", "invented number in narration",
                 "wrong fact in narration", "two operations swapped", "quiz operation dropped")
MIN_OVERALL = 0.965  # measured 0.970 when Milestone 7 landed (0.927 with the Milestone 6 verifier)


@pytest.fixture(scope="module")
def results():
    out = defaultdict(list)
    for name in EXAMPLES:
        for mutant, caught in mutants.run(load(name)):
            out[mutant.operator].append((name, mutant.where, caught))
    return out


@pytest.mark.parametrize("operator", ALWAYS_CAUGHT)
def test_these_mistakes_are_always_caught(results, operator):
    missed = [f"{plan} ({where})" for plan, where, caught in results[operator] if not caught]
    assert results[operator] and not missed, f"{operator} survived in: {', '.join(missed)}"


def test_overall_catch_rate(results):
    rows = [caught for rows in results.values() for *_, caught in rows]
    assert len(rows) > 500
    assert sum(rows) / len(rows) >= MIN_OVERALL


def test_equivalent_mutants_are_not_counted():
    lesson = load("dijkstra")
    every = mutants.run(lesson, keep_equivalent=True)
    counted = mutants.run(lesson)
    assert len(counted) < len(every)  # its first quiz question's last operation does not change the answer
    assert mutants.trace(lesson) == mutants.trace(lesson.model_copy(deep=True))
