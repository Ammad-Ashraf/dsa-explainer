"""Generate more saved lesson plans with a language model (the provider in use: Settings or .env).

    python backend/scripts/generate_plans.py bubble_sort dijkstra --levels beginner advanced
    python backend/scripts/generate_plans.py --all --out plans-draft

Each plan goes through the same planner, quiz writer and verifier as the app,
and is saved only if it passes, with its provenance (model, date). Review a
draft before moving it into dsa_explainer/plans/: the verifier vouches for the
facts, a person should vouch for the teaching.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dsa_explainer import algorithms  # noqa: E402
from dsa_explainer.authoring import llm, planner, quiz  # noqa: E402
from dsa_explainer.core.verifier import verify_lesson  # noqa: E402


def topic_for(cls, preset_name: str, preset) -> str:
    return f"Explain {cls.TITLE.lower()} step by step, using this data: {preset} ({preset_name})"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("names", nargs="*", help="algorithm ids (see dsa_explainer/algorithms)")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--levels", nargs="+", default=["beginner"], choices=["beginner", "intermediate", "advanced"])
    parser.add_argument("--out", default=str(ROOT / "plans-draft"), help="folder for the drafts")
    args = parser.parse_args()
    names = [cls.NAME for cls in algorithms.ALL] if args.all else args.names
    if not names:
        parser.error("name one or more algorithms, or use --all")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    model = llm.current().settings.model
    failures = 0
    for name in names:
        cls = algorithms.get(name)
        preset_name, preset = next(iter(cls.PRESETS.items()))
        for level in args.levels:
            label = f"{name}-{level}"
            try:
                lesson, rejected = planner.plan_lesson(topic_for(cls, preset_name, preset), level, log=lambda *a: None)
                lesson.quiz = quiz.make_quiz(lesson, log=lambda *a: None)
                report = verify_lesson(lesson)
                if not report.ok:
                    raise RuntimeError(report.errors[0])
            except Exception as exc:  # keep going with the next plan
                print(f"FAIL {label}: {llm.redact(str(exc))[:200]}")
                failures += 1
                continue
            lesson.provenance = {"author": f"language model {model}", "written": date.today().isoformat(),
                                 "checked_by": "DSA Explainer verifier (scripts/generate_plans.py)",
                                 "rejected_attempts": len(rejected)}
            (out / f"{label}.json").write_text(lesson.model_dump_json(indent=2, exclude_none=True) + "\n",
                                               encoding="utf-8")
            print(f"ok   {label}: {report.checks} checks, {len(rejected)} attempt(s) rejected")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
