"""Evaluation harness: plan and quiz every chosen algorithm with every chosen provider and JSON mode.

    python backend/scripts/eval_harness.py --algorithms stack,dijkstra --modes json_schema,json_object
    python backend/scripts/eval_harness.py --providers gemini,groq --max-calls 30
    python backend/scripts/eval_harness.py --dry-run          # no network: replays the saved plans

For each (provider, JSON mode, algorithm) it asks the planner for a lesson, the
quiz writer for questions, and records: whether a verified lesson came out, how
many attempts the verifier needed, how long each language-model call took, and
whether any call timed out. Every call is counted and the run stops at
--max-calls, because free tiers allow only a few requests a day.

Results: one JSON line per run in outputs/eval/<timestamp>.jsonl, and a summary
by JSON mode in docs/research/eval-<date>.md (or the path given with --report).
`scripts/live_eval.py` stays as the fixed course evaluation; this harness is the
general one.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dsa_explainer import algorithms, config  # noqa: E402
from dsa_explainer.authoring import llm, planner, providers, quiz  # noqa: E402
from dsa_explainer.core.verifier import verify_lesson  # noqa: E402

DEFAULT_ALGORITHMS = ("stack", "bst", "dijkstra", "quick_sort")


class Budget(RuntimeError):
    """The run reached --max-calls."""


class CallLog:
    """Wraps llm.Client.chat to time and count every request, by purpose (plan or quiz)."""

    def __init__(self, max_calls: int) -> None:
        self.calls: list[dict] = []
        self.max_calls = max_calls
        self.purpose = ""
        self._original = llm.Client.chat

    def __enter__(self):
        log = self

        def chat(client, messages, temperature=None, schema=None, timeout=None):
            if len(log.calls) >= log.max_calls:
                raise Budget(f"stopped at --max-calls {log.max_calls}")
            started = time.perf_counter()
            entry = {"purpose": log.purpose, "mode": client.mode, "model": client.model_in_use()}
            try:
                reply = log._original(client, messages, temperature, schema, timeout)
                entry["ok"] = True
                return reply
            except Exception as exc:
                entry.update(ok=False, error=f"{type(exc).__name__}: {str(exc)[:160]}",
                             timeout="timed out" in str(exc).lower() or "timeout" in type(exc).__name__.lower())
                raise
            finally:
                entry["seconds"] = round(time.perf_counter() - started, 2)
                log.calls.append(entry)

        llm.Client.chat = chat
        return self

    def __exit__(self, *exc) -> None:
        llm.Client.chat = self._original


def topic_for(name: str) -> str:
    cls = algorithms.get(name)
    preset_name, data = next(iter(cls.PRESETS.items()))
    return f"Explain {cls.TITLE.lower()} step by step on this data ({preset_name}): {json.dumps(data)}"


def run_one(settings: llm.LLMSettings, name: str, calls: CallLog) -> dict:
    row = {"provider": settings.provider, "model": settings.model, "mode": settings.structured, "algorithm": name}
    first = len(calls.calls)
    with llm.use(settings):
        calls.purpose = "plan"
        started = time.perf_counter()
        try:
            lesson, rejected = planner.plan_lesson(topic_for(name), "beginner", log=lambda *a, **k: None)
        except Budget:
            raise
        except Exception as exc:
            row.update(result="no lesson", error=str(exc)[:200], plan_seconds=round(time.perf_counter() - started, 1))
            return _calls(row, calls, first)
        row.update(result="lesson", attempts=len(rejected) + 1, structure=lesson.structure,
                   plan_seconds=round(time.perf_counter() - started, 1), rejected=[r[:160] for r in rejected])
        calls.purpose = "quiz"
        started = time.perf_counter()
        try:
            questions = quiz.make_quiz(lesson, log=lambda *a, **k: None)
            row.update(quiz="ok", questions=len(questions),
                       builtin=sum(q.question.startswith(("After all the steps", "True or false", "How many"))
                                   for q in questions))
            lesson.quiz = questions
        except Budget:
            raise
        except Exception as exc:
            row.update(quiz="failed", quiz_error=str(exc)[:200])
        row["quiz_seconds"] = round(time.perf_counter() - started, 1)
        row["verified"] = verify_lesson(lesson).ok
    return _calls(row, calls, first)


def _calls(row: dict, calls: CallLog, first: int) -> dict:
    mine = calls.calls[first:]
    row["calls"] = mine
    row["timeouts"] = sum(bool(c.get("timeout")) for c in mine)
    return row


def settings_for(provider: str) -> llm.LLMSettings:
    if provider == "active":
        settings = llm.active_settings()
    else:
        data = providers.resolve(provider)
        settings = llm.LLMSettings.from_dict(data) if data else None
    if settings is None:
        raise SystemExit(f"provider '{provider}' has no key or model saved; set it up in Settings first")
    return settings


def summary(rows: list[dict]) -> str:
    def med(values):
        values = [v for v in values if v is not None]
        return f"{statistics.median(values):.0f} s" if values else "-"

    lines = ["| Provider | Model | JSON mode | Runs | Verified lessons | First-try plans | Plan time (median) | "
             "Plan call (median) | Quiz time (median) | Quiz from the model | Failed calls | Timeouts |",
             "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    groups: dict[tuple, list] = {}
    for r in rows:
        groups.setdefault((r["provider"], r["model"], r["mode"]), []).append(r)
    for (provider, model, mode), rs in groups.items():
        lessons = [r for r in rs if r["result"] == "lesson"]
        plan_calls = [c["seconds"] for r in rs for c in r["calls"] if c["purpose"] == "plan" and c["ok"]]
        model_quiz = sum(r.get("questions", 0) - r.get("builtin", 0) for r in lessons)
        lines.append(
            f"| {provider} | `{model}` | {mode} | {len(rs)} | {sum(r.get('verified', False) for r in lessons)} | "
            f"{sum(r.get('attempts') == 1 for r in lessons)} | {med([r.get('plan_seconds') for r in lessons])} | "
            f"{med(plan_calls)} | {med([r.get('quiz_seconds') for r in lessons])} | {model_quiz} | "
            f"{sum(not c['ok'] for r in rs for c in r['calls'])} | {sum(r['timeouts'] for r in rs)} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--algorithms", default=",".join(DEFAULT_ALGORITHMS))
    parser.add_argument("--providers", default="active", help="saved provider ids, comma-separated, or 'active'")
    parser.add_argument("--modes", default="json_schema,json_object", help=f"from: {', '.join(llm.MODES)}")
    parser.add_argument("--max-calls", type=int, default=16)
    parser.add_argument("--pause", type=float, default=8.0, help="seconds between runs (free-tier rate limits)")
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true", help="no network: the saved plans are the replies")
    parser.add_argument("--summarise", type=Path, help="print the summary of an earlier run's .jsonl and stop")
    args = parser.parse_args(argv)
    if args.summarise:
        print(summary([json.loads(line) for line in args.summarise.read_text(encoding="utf-8").splitlines()]))
        return 0
    names = [algorithms.resolve(n.strip()) for n in args.algorithms.split(",") if n.strip()]
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    if any(m not in llm.MODES for m in modes):
        raise SystemExit(f"modes must be from: {', '.join(llm.MODES)}")
    if args.dry_run:
        _dry_run(names)
        provider_settings = [llm.LLMSettings(provider="dry-run", base_url="http://dry-run", api_key="", model="saved")]
    else:
        provider_settings = [settings_for(p.strip()) for p in args.providers.split(",") if p.strip()]

    out_dir = config.OUTPUT_DIR / "eval"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    jsonl = out_dir / f"{stamp}.jsonl"
    rows: list[dict] = []
    with CallLog(args.max_calls) as calls:
        try:
            for settings in provider_settings:
                for mode in modes:
                    for name in names:
                        row = run_one(dataclasses.replace(settings, structured=mode), name, calls)
                        rows.append(row)
                        with jsonl.open("a", encoding="utf-8") as f:
                            f.write(json.dumps(row) + "\n")
                        print(f"{row['provider']} {mode} {name}: {row['result']}, plan {row.get('plan_seconds')} s, "
                              f"quiz {row.get('quiz_seconds')} s, {len(row['calls'])} call(s)", flush=True)
                        if not args.dry_run:
                            time.sleep(args.pause)
        except Budget as exc:
            print(exc)
    table = summary(rows)
    report = args.report or ROOT.parent / "docs" / "research" / f"eval-{datetime.now():%Y-%m-%d}.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(f"# Evaluation run {stamp}\n\nAlgorithms: {', '.join(names)}. Command: "
                      f"`python backend/scripts/eval_harness.py {' '.join(argv if argv is not None else sys.argv[1:])}`"
                      f"\n\n{table}\n\nRaw results: `outputs/eval/{jsonl.name}`.\n", encoding="utf-8")
    print(table)
    print("written:", report)
    return 0


def _dry_run(names: list[str]) -> None:
    """Replace the network with the saved plans, so the harness itself can be tested offline."""
    from dsa_explainer.core.lesson import Lesson

    def fake(client, messages, temperature=None, schema=None, timeout=None):
        text = " ".join(m["content"] for m in messages)
        if "multiple-choice quiz" in text:
            return json.dumps({"questions": []})  # the built-in questions fill in
        topic = next(m["content"] for m in messages if m["role"] == "user").lower()
        name = next(n for n in names if algorithms.get(n).TITLE.lower() in topic)
        lesson = Lesson.model_validate_json((config.PLANS_DIR / f"{name}.json").read_text(encoding="utf-8"))
        return lesson.model_dump_json()

    llm.Client.chat = fake


if __name__ == "__main__":
    sys.exit(main())
