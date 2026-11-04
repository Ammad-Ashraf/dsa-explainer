"""DSA Explainer web app.   Run:  python app.py   then open http://127.0.0.1:7860"""

from __future__ import annotations

import sys
import traceback

import gradio as gr

from dsa_explainer import config, llm, pipeline
from dsa_explainer.lesson import Lesson, scene_labels
from dsa_explainer.structures import DISPLAY_NAMES
from dsa_explainer.verifier import answer_index

QUALITIES = {"Draft (480p, faster)": "draft", "Standard (720p)": "standard"}
EXAMPLE_TOPICS = [
    ["How does a stack work?", "beginner"],
    ["Show how a queue handles print jobs", "intermediate"],
    ["How do you insert into the middle of a linked list?", "beginner"],
    ["Insert 8, 3, 10, 1, 6, 14 into a BST, then delete 3", "intermediate"],
    ["Show BFS on this graph: A-B, A-C, B-D, C-E, D-E, start at A", "beginner"],
]
SAVED_PLANS = sorted(p.stem for p in config.EXAMPLES_DIR.glob("*.json"))


def _logger(progress: gr.Progress):
    state = {"at": 0.0}

    def log(message: str, fraction: float | None = None) -> None:
        if fraction is not None:
            state["at"] = fraction
        progress(state["at"], desc=message)

    return log


def _quiz_markdown(lesson: Lesson) -> str:
    parts = ["### Quiz"]
    for i, q in enumerate(lesson.quiz, 1):
        right = answer_index(lesson, q)
        options = "\n".join(f"- {'ABCD'[j]}. {o}" for j, o in enumerate(q.options))
        parts.append(f"**{i}. {q.question}**\n\n{options}\n\n<details><summary>Show answer</summary>\n\n"
                     f"**{'ABCD'[right]}. {q.options[right]}**: {q.explanation} "
                     f"*(checked by running the operations on a real data structure)*\n\n</details>")
    return "\n\n".join(parts)


def _scene_list(lesson: Lesson) -> str:
    names = [f"{label} ({s.op.describe()})" if s.op else label for label, s in zip(scene_labels(lesson), lesson.scenes)]
    return "**Parts you can change:** " + ", ".join(names)


def _show(result: dict):
    lesson, report = result["lesson"], result["report"]
    lines = [
        f"### Verified: {report.checks} checks passed",
        f"Every step was run on a real {DISPLAY_NAMES[lesson.structure].lower()}. The claimed states, the facts "
        f"in the narration and the quiz answers all match it.",
    ]
    if result.get("rejected"):
        lines.append(f"**The verifier sent {len(result['rejected'])} plan(s) back before accepting one:**\n"
                     + "\n".join(f"- {r}" for r in result["rejected"]))
    if "changed" in result:
        lines.append(f"**Revision** \"{result['request']}\" changed: {', '.join(result['changed'])}.")
    lines.append(f"**Video:** {result['seconds']:.0f} s, {result['clips']} clips: {len(result['rendered'])} drawn "
                 f"now, {result['reused']} reused from the cache.")
    timing = []
    if "plan_seconds" in result:
        timing += [f"planning {result['plan_seconds']:.0f} s ({llm.model_in_use()})",
                   f"quiz {result['quiz_seconds']:.0f} s"]
    timing += [f"voice {result['voice_seconds']:.0f} s",
               f"voice and drawing together {result['build_seconds']:.0f} s"]
    lines.append("**Time:** " + ", ".join(timing))
    current = {"folder": str(result["folder"]), "version": result["version"]}
    return (str(result["video"]), "\n\n".join(lines), _quiz_markdown(lesson),
            lesson.model_dump(mode="json"), current, _scene_list(lesson))


def _run(job):
    try:
        return _show(job())
    except gr.Error:
        raise
    except Exception as exc:  # shown to the user as a message, logged for us
        traceback.print_exc()
        raise gr.Error(str(exc)) from exc


def create(topic, level, quality, progress=gr.Progress()):
    if not topic.strip():
        raise gr.Error("Type a topic first, for example: how does a queue work?")
    return _run(lambda: pipeline.make_lesson(topic, level, QUALITIES[quality], _logger(progress)))


def play_saved(name, quality, progress=gr.Progress()):
    path = config.EXAMPLES_DIR / f"{name}.json"
    return _run(lambda: pipeline.from_file(path, QUALITIES[quality], _logger(progress)))


def revise(request, current, quality, progress=gr.Progress()):
    if not current:
        raise gr.Error("Make a video first.")
    return _run(lambda: pipeline.revise_lesson(current["folder"], current["version"], request,
                                               QUALITIES[quality], _logger(progress)))


with gr.Blocks(title="DSA Explainer", analytics_enabled=False) as demo:
    gr.Markdown("# DSA Explainer\nType a data-structures topic and get a narrated animation with a quiz at the end. "
                "Every step is checked by running the real data structure before anything is drawn.")
    if not config.LLM_API_KEY:
        gr.Markdown("**No LLM API key found.** Copy `.env.example` to `.env` and add a key to plan new lessons. "
                    "Saved lessons below work without one.")
    current = gr.State(None)
    with gr.Row():
        with gr.Column(scale=2):
            topic = gr.Textbox(label="What do you want to learn?", placeholder="e.g. How does a queue work?", lines=2)
            with gr.Row():
                level = gr.Dropdown(["beginner", "intermediate", "advanced"], value="beginner", label="Level")
                quality = gr.Dropdown(list(QUALITIES), value=list(QUALITIES)[0], label="Video quality")
            make = gr.Button("Make video", variant="primary")
            gr.Examples(EXAMPLE_TOPICS, inputs=[topic, level], label="Try one of these")
            with gr.Accordion("No API key? Make a video from a saved lesson plan", open=False):
                saved = gr.Dropdown(SAVED_PLANS, value=SAVED_PLANS[0] if SAVED_PLANS else None, label="Saved plan")
                play = gr.Button("Make video from saved plan")
        with gr.Column(scale=3):
            video = gr.Video(label="Lesson", interactive=False, autoplay=True)
            with gr.Row():
                request = gr.Textbox(label="Change part of the video", scale=4,
                                     placeholder="e.g. slow down step 4, or explain step 2 for a beginner")
                apply = gr.Button("Apply change", scale=1)
            scenes = gr.Markdown()
    with gr.Row():
        report = gr.Markdown()
        quiz_box = gr.Markdown()
    with gr.Accordion("Lesson plan (JSON written by the LLM, after verification)", open=False):
        plan = gr.JSON()

    outputs = [video, report, quiz_box, plan, current, scenes]
    make.click(create, [topic, level, quality], outputs)
    topic.submit(create, [topic, level, quality], outputs)
    play.click(play_saved, [saved, quality], outputs)
    apply.click(revise, [request, current, quality], outputs)
    request.submit(revise, [request, current, quality], outputs)


if __name__ == "__main__":
    # one job at a time: rendering and the voice model are shared
    demo.queue(default_concurrency_limit=1).launch(inbrowser="--no-browser" not in sys.argv,
                                                   allowed_paths=[str(config.OUTPUT_DIR)])
