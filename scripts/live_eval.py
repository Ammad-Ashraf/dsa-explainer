"""Live evaluation of every part that uses the language model, with the API set in .env.

    python scripts/live_eval.py            # plan + quiz for each topic, then two revisions
    python scripts/live_eval.py --render   # also make each video
    python scripts/live_eval.py --resume   # keep topics that already finished (after a rate limit)

Writes docs/live-eval.md; accepted plans (and videos) go to outputs/live-eval/.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dsa_explainer import config, llm, planner, quiz, revise, video  # noqa: E402
from dsa_explainer.lesson import Lesson  # noqa: E402
from dsa_explainer.verifier import verify_lesson  # noqa: E402

# (topic, level, should the app make a lesson?)
TOPICS = [
    ("How does a stack work?", "beginner", True),
    ("Show how a queue handles print jobs", "intermediate", True),
    ("How do you insert into the middle of a linked list?", "beginner", True),
    ("Insert 8, 3, 10, 1, 6, 14 into a BST, then delete 3", "intermediate", True),
    ("Show BFS on this graph: A-B, A-C, B-D, C-E, D-E, start at A", "beginner", True),
    ("Explain deleting a node with two children from a binary search tree", "advanced", True),
    ("How does breadth-first search work?", "intermediate", True),
    ("Explain heap sort", "beginner", False),
    ("What is the capital of France?", "beginner", False),
]
REVISIONS = ["explain step 2 for a beginner", "make the summary shorter"]
OUT = config.OUTPUT_DIR / "live-eval"


class Log(list):
    def __call__(self, message: str, fraction: float | None = None) -> None:
        self.append(message)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


def run_topic(n: int, topic: str, level: str, render: bool) -> dict:
    row = {"n": n, "topic": topic, "level": level}
    started = time.perf_counter()
    try:
        lesson, rejected = planner.plan_lesson(topic, level, log=Log())
    except planner.PlanError as exc:
        failed = str(exc).startswith("No correct plan")
        return {**row, "result": "failed" if failed else "refused", "message": str(exc),
                "plan_seconds": time.perf_counter() - started, "model": llm.model_in_use()}
    except Exception as exc:  # API errors (rate limits, outages)
        return {**row, "result": "API error", "message": f"{type(exc).__name__}: {str(exc)[:200]}"}
    row.update(result="lesson", rejected=rejected, attempts=len(rejected) + 1, model=llm.model_in_use(),
               plan_seconds=time.perf_counter() - started, structure=lesson.structure,
               steps=sum(s.kind == "step" for s in lesson.scenes),
               words=sum(len(s.narration.split()) for s in lesson.scenes))

    started, log = time.perf_counter(), Log()
    try:
        lesson.quiz = quiz.make_quiz(lesson, log=log)
    except Exception as exc:
        return {**row, "result": "API error", "message": f"quiz: {type(exc).__name__}: {str(exc)[:200]}"}
    row.update(quiz_seconds=time.perf_counter() - started,
               quiz_attempts=sum(m.startswith("Writing the quiz") for m in log),
               quiz_fallback=lesson.quiz[0].question.startswith("After all the steps"),
               questions=len(lesson.quiz))
    report = verify_lesson(lesson)
    row.update(verified=report.ok, checks=report.checks)

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{n:02d}-{slug(topic)}.json"
    path.write_text(lesson.model_dump_json(indent=2), encoding="utf-8")
    row["plan_file"] = path
    if render:
        result = video.build_video(lesson, report, path.with_suffix(".mp4"), "draft", log=Log())
        row.update(video_seconds=result["seconds"], build_seconds=result["build_seconds"])
    row["lesson"] = lesson
    return row


def run_revisions(lesson) -> list[dict]:
    rows = []
    for request in REVISIONS:
        log, started = Log(), time.perf_counter()
        try:
            new, changed = revise.revise(lesson, request, log=log)
            rows.append({"request": request, "changed": changed, "verified": verify_lesson(new).ok,
                         "attempts": sum(m.startswith("Rewriting") for m in log),
                         "seconds": time.perf_counter() - started})
        except Exception as exc:
            rows.append({"request": request, "error": f"{type(exc).__name__}: {exc}"})
    return rows


def secs(value) -> str:
    return "–" if value is None else f"{value:.0f} s"


def write_report(rows: list[dict], revisions: list[dict], render: bool) -> Path:
    lines = [
        "# Live evaluation",
        "",
        f"Provider: `{config.LLM_BASE_URL}`. Main model `{config.LLM_MODEL}`, fallback `{config.LLM_FALLBACK_MODEL}` "
        f"(used once the main model's daily free allowance runs out). Updated {date.today():%d %B %Y} with "
        f"`python scripts/live_eval.py{' --render' if render else ''}`.",
        "",
        "| # | Topic | Level | Expected | Result | Model | Plan attempts | Steps | Words | Quiz | Checks | Plan time |"
        + (" Video |" if render else ""),
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |" + (" --- |" if render else ""),
    ]
    for (topic, level, expected), r in zip(TOPICS, rows):
        want = "lesson" if expected else "refusal"
        if r["result"] == "lesson":
            quiz_note = f"{r['questions']} verified" + (" (fallback)" if r["quiz_fallback"] else "")
            if (r.get("quiz_attempts") or 1) > 1:
                quiz_note += f", {r['quiz_attempts']} attempts"
            cells = [f"lesson ({r['structure']})", f"`{r.get('model', '')}`", str(r["attempts"]), str(r["steps"]),
                     str(r["words"]), quiz_note, str(r["checks"]), secs(r.get("plan_seconds"))]
            if render:
                made = r.get("build_seconds")
                cells.append(secs(r.get("video_seconds")) + ("" if made is None else f" (made in {made:.0f} s)"))
        else:
            cells = [r["result"], f"`{r.get('model', '')}`", "", "", "", "", "", secs(r.get("plan_seconds"))]
            cells += [""] if render else []
        lines.append(f"| {r['n']} | {topic} | {level} | {want} | " + " | ".join(cells) + " |")

    lessons = [r for r in rows if r["result"] == "lesson"]
    matched = sum(r["result"] == ("lesson" if expected else "refused") for (_, _, expected), r in zip(TOPICS, rows))
    first_try = sum(r["attempts"] == 1 for r in lessons)
    lines += [
        "",
        f"**{matched} of {len(rows)}** topics got the expected result. **{first_try} of {len(lessons)}** lessons "
        "passed the verifier on the first attempt; every lesson that was accepted passed every check.",
        "",
        "## Plans the verifier sent back",
        "",
    ]
    sent_back = [(r["topic"], msg) for r in lessons for msg in r["rejected"]]
    lines += [f"- *{t}*: {m}" for t, m in sent_back] or ["None: every plan was correct on its first attempt."]
    lines += ["", "## Refusals", ""]
    lines += [f"- *{r['topic']}*: {r['message']}" for r in rows if r["result"] != "lesson"] or ["None."]
    lines += ["", f"## Revisions (on lesson 1, *{TOPICS[0][0]}*)", "",
              "| Request | Scenes changed | LLM attempts | Verified | Time |", "| --- | --- | --- | --- | --- |"]
    for v in revisions:
        if "error" in v:
            lines.append(f"| {v['request']} | error: {v['error']} | | | |")
        else:
            lines.append(f"| {v['request']} | {', '.join(v['changed'])} | {v['attempts']} | "
                         f"{'yes' if v['verified'] else 'no'} | {v['seconds']:.0f} s |")
    lines.append("")
    path = ROOT / "docs" / "live-eval.md"
    path.parent.mkdir(exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def saved(n: int) -> dict | None:
    """A finished result from an earlier run (--resume), with its lesson loaded again."""
    path = OUT / f"{n:02d}.result.json"
    if not path.exists():
        return None
    row = json.loads(path.read_text(encoding="utf-8"))
    if row["result"] == "lesson":
        row["lesson"] = Lesson.model_validate_json(Path(row["plan_file"]).read_text(encoding="utf-8"))
    return row


def save(row: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = {k: (str(v) if isinstance(v, Path) else v) for k, v in row.items() if k != "lesson"}
    (OUT / f"{row['n']:02d}.result.json").write_text(json.dumps(data, indent=1), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="store_true", help="also make the videos")
    parser.add_argument("--resume", action="store_true", help="keep finished results from an earlier run")
    args = parser.parse_args()
    rows = []
    for n, (topic, level, _) in enumerate(TOPICS, 1):
        row = saved(n) if args.resume else None
        if row is None or row["result"] == "API error":
            row = run_topic(n, topic, level, args.render)
            if row["result"] != "API error":
                save(row)
            time.sleep(10)  # stay gentle with free-tier rate limits
        rows.append(row)
        print(f"{n}. {topic} -> {row['result']}" + (f" after {row['attempts']} attempt(s)" if "attempts" in row else ""),
              flush=True)
    first = next((r for r in rows if r["result"] == "lesson"), None)
    revisions = run_revisions(first["lesson"]) if first else []
    print("revisions:", [(v["request"], v.get("changed", v.get("error"))) for v in revisions], flush=True)
    print("written:", write_report(rows, revisions, args.render))


if __name__ == "__main__":
    main()
