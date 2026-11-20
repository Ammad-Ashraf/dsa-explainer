"""Mutation testing of the verifier over every saved plan; prints a Markdown report.

    python backend/scripts/mutation_report.py                 # the table, by operator
    python backend/scripts/mutation_report.py --survivors     # also list every mutant that was not caught

See dsa_explainer/core/mutants.py for the operators.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dsa_explainer import config  # noqa: E402
from dsa_explainer.core import mutants  # noqa: E402
from dsa_explainer.core.lesson import Lesson  # noqa: E402


def collect() -> dict[str, list]:
    results: dict[str, list] = defaultdict(list)
    for path in sorted(config.PLANS_DIR.glob("*.json")):
        lesson = Lesson.model_validate_json(path.read_text(encoding="utf-8"))
        for mutant, caught in mutants.run(lesson):
            results[mutant.operator].append((path.stem, mutant.where, caught))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--survivors", action="store_true")
    args = parser.parse_args()
    results = collect()
    total = sum(len(r) for r in results.values())
    caught = sum(c for r in results.values() for *_, c in r)
    print("| Mistake planted | Mutants | Caught | Catch rate |")
    print("| --- | ---: | ---: | ---: |")
    for operator, rows in results.items():
        n, c = len(rows), sum(r[2] for r in rows)
        print(f"| {operator} | {n} | {c} | {100 * c / n:.0f}% |")
    print(f"| **all** | **{total}** | **{caught}** | **{100 * caught / total:.1f}%** |")
    if args.survivors:
        print("\nSurvivors:")
        for operator, rows in results.items():
            for plan, where, ok in rows:
                if not ok:
                    print(f"- {operator}: {plan}, {where}")


if __name__ == "__main__":
    main()
