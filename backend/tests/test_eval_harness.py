"""The evaluation harness runs end to end offline (--dry-run replays the saved plans)."""

import importlib.util
import json
from pathlib import Path

from dsa_explainer import config
from dsa_explainer.authoring import llm

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "eval_harness.py"


def load_harness():
    spec = importlib.util.spec_from_file_location("eval_harness", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dry_run_writes_results_and_a_summary_by_mode(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path / "outputs")
    monkeypatch.setattr(llm.Client, "chat", llm.Client.chat)  # the dry run replaces it; restored afterwards
    harness = load_harness()
    report = tmp_path / "eval.md"
    assert harness.main(["--dry-run", "--algorithms", "stack,bst", "--modes", "json_object,none",
                         "--report", str(report)]) == 0
    rows = [json.loads(line) for line in next((tmp_path / "outputs" / "eval").glob("*.jsonl")).read_text().splitlines()]
    assert [(r["mode"], r["algorithm"]) for r in rows] == [("json_object", "stack"), ("json_object", "bst"),
                                                          ("none", "stack"), ("none", "bst")]
    assert all(r["result"] == "lesson" and r["verified"] and r["attempts"] == 1 for r in rows)
    assert all(c["purpose"] in ("plan", "quiz") and c["ok"] for r in rows for c in r["calls"])
    text = report.read_text(encoding="utf-8")
    assert "| dry-run | `saved` | json_object | 2 | 2 | 2 |" in text


def test_the_call_budget_stops_the_run(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path / "outputs")
    monkeypatch.setattr(llm.Client, "chat", llm.Client.chat)
    harness = load_harness()
    assert harness.main(["--dry-run", "--algorithms", "stack,bst,queue", "--modes", "json_object",
                         "--max-calls", "3", "--report", str(tmp_path / "eval.md")]) == 0
    rows = [json.loads(line) for line in next((tmp_path / "outputs" / "eval").glob("*.jsonl")).read_text().splitlines()]
    assert sum(len(r["calls"]) for r in rows) <= 3
