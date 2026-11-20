# DSA Explainer

**NLP Course Project, Fall 2026 — Project 1: Data Structure Explainer**

| Name | Registration number |
| --- | --- |
| Ahmed Javaid | 22i-2530 |
| Ammad Ashraf | 22i-2470 |

A learner types a topic such as *"how does a queue work"* or *"show BFS on this graph: A-B, A-C, B-D, start at A"*.
DSA Explainer plans a lesson, checks every step by running the real data structure, writes and speaks the
narration, animates it, and exports a video that ends with a short quiz. The learner can then say
*"slow down step 4"* or *"explain it for a beginner"*, and only that part of the video changes.

Covered: **stacks, queues, linked lists, binary search trees, and breadth-first search on a graph**.

**Demo video:** *add the Loom link*

> **Where this is going.** The course version is submitted from `main`. This branch turns DSA Explainer into an
> open-source, local-first platform: a React frontend, bring-your-own LLM key, newer local voice models, many more
> algorithms, and richer verified animations. The plan is in [docs/roadmap/](docs/roadmap/):
> [the ideas](docs/roadmap/vision.md) and [the milestones](docs/roadmap/milestones.md).

## Documents

| Document | What it is |
| --- | --- |
| [Vision](docs/roadmap/vision.md) and [milestones](docs/roadmap/milestones.md) | Where the project goes after the course, and in what order |
| [Report](docs/course/report.md) ([PDF](docs/course/report.pdf)) | The project report: Complex Computing Problem analysis (problem statement, complexity drivers, design justification, trade-offs, societal and ethical impact), core modules, setup, technical details, testing and evaluation |
| [Architecture diagram](docs/course/architecture.png) | The system architecture (drawn by `backend/scripts/make_diagram.py`) |
| [Live evaluation](docs/course/live-eval.md) | Results of nine real requests to the language model (`backend/scripts/live_eval.py`) |
| [Loom video guide](docs/course/loom-video-guide.md) | Script and checklist for the 2 to 3 minute demo video |
| [AI prompts](docs/course/ai-prompts.md) | The prompts we gave our AI coding assistant |
| [Submission checklist](docs/course/submission-checklist.md) | What is done and what is left before submitting |

The course documents in `docs/course/` describe the submitted version on `main`, so their file paths use that
branch's layout (`dsa_explainer/`, `app.py` and `scripts/` at the top level).

## Repository layout

```
backend/                    Python: the whole pipeline and the local API, run on your computer
  dsa_explainer/
    algorithms/             22 simulators the verifier trusts, with their catalogue data
    core/                   lesson schema and step verifier (no AI, no I/O)
    authoring/              everything a language model writes: planner, quiz, revisions, providers
    media/                  local voice (Kokoro), animation (Manim, one view per picture), joining clips
    api/                    FastAPI app and the job runner (live progress over Server-Sent Events)
    plans/                  verified lesson plans that play without an API key
    pipeline.py             plan -> verify -> quiz -> voice -> animation -> video
    config.py, settings.py  settings from .env and from the app
  scripts/                  model download, plan authoring, live evaluation, diagram, report PDF
  tests/
frontend/                   React + TypeScript web app (Vite), served by the backend once built
docs/
  roadmap/                  vision and milestones for the open-source platform
  course/                   the course submission: report, diagram, live evaluation, Loom guide
.env.example                copy to .env and add an API key
models/  outputs/  cache/   created at run time, not in git
```

## Models, APIs and what runs locally

| Part | Model / tool | Where it runs |
| --- | --- | --- |
| Lesson planning, narration text, quiz questions, revisions | Any OpenAI-compatible LLM API; default **Gemini 3.5 Flash** (free tier), switching to **Gemini 3.5 Flash-Lite** when the daily free allowance runs out. Groq, Claude, OpenAI or a local Ollama model work by changing `.env` | API (allowed by the brief) |
| Step verifier, quiz answer checking | Plain Python simulators (`dsa_explainer/algorithms/`) | Local |
| Text to speech | **Kokoro-82M** (ONNX, CPU) via `kokoro-onnx` | **Local** (required by the brief) |
| Animation | **Manim Community 0.22** (Cairo renderer, no LaTeX) | Local |
| Joining clips | ffmpeg (bundled by `imageio-ffmpeg`) | Local |
| User interface | React web app talking to a local FastAPI server | Local |

## Architecture

![DSA Explainer system architecture](docs/course/architecture.png)

**The key idea: the language model never draws and never has the last word on facts.**
It writes a *structured plan*: the starting data, one operation per step (`push(7)`, `insert(6)`, `bfs_step()`),
what it believes the state is after each step (`claimed_state`), and the narration. The verifier then runs
those operations on real Python data structures. If an operation is impossible, a claimed state is wrong, or the
narration says something false ("the top is now 9"), the plan goes back to the model with the true state, up to
four attempts. If it still fails, **no video is made**, because a wrong video is worse than no video. The renderer
only ever draws the verifier's snapshots of the real structure, never the model's claims.

### The six core modules

| Module (brief) | File | How it works |
| --- | --- | --- |
| 1. Lesson planner | `authoring/planner.py`, `core/lesson.py` | Topic + level → JSON plan (intro, 4–8 steps, summary). Validated with Pydantic, then by the verifier; errors are fed back for repair. |
| 2. Animation renderer | `media/render.py` | Manim. Each structure has a drawer that turns a snapshot into named shapes; one generic `morph` animates any step by moving shapes that exist before and after, fading out removed ones and fading in new ones. Paths (BST comparisons, list walks) are highlighted first. |
| 3. Step verifier | `core/verifier.py`, `algorithms/` | Runs every operation; compares `claimed_state` with the true state; checks narration claims (top/front/rear/head/tail/root/size/current node) and flags any number that is not in the structure or the operation; checks the video will last over 30 s. |
| 4. Narration and voice | `media/voice.py`, `media/video.py` | Kokoro-82M on the CPU. Each scene's audio is made first and the animation is timed to it, so voice and picture stay in sync. |
| 5. Quiz generator | `authoring/quiz.py` | The LLM writes multiple-choice questions that carry their own operations; each answer is checked by running them. Wrong questions are sent back; if none survive, a question is built from the lesson itself. |
| 6. Revision control | `authoring/revise.py`, `media/video.py` | "Slow down / speed up step N" is handled by rules; other requests go to the LLM, which may only change narration, captions, speed and summary points. The result is verified again. Clips are cached by a hash of their content, so only changed scenes are re-rendered. |

All module paths are inside `backend/dsa_explainer/`. `pipeline.py` ties the modules together; `api/` serves
them to the web app in `frontend/`.

## Setup (Windows, macOS or Linux; Python 3.11 to 3.13)

You need Python 3.11 to 3.13 and Node.js 20 or newer. Run these from the repository root:

```bash
python -m venv .venv
.venv\Scripts\activate                      # macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/scripts/download_models.py   # Kokoro voice, ~350 MB, once
cd frontend && npm install && npm run build && cd ..
```

## Run

```bash
cd backend
python -m dsa_explainer serve --open
```

The app opens at http://127.0.0.1:8000. Every lesson in the **Library** plays without an API key. To make lessons
from your own topics, open **Settings** and add a key for any provider (Gemini and Groq have free tiers; Ollama runs
on your computer with no key). A key in `.env` works too (copy `.env.example`).

In the **Studio**, type a topic and press **Make my lesson**. The pipeline's progress appears on the left, and each
scene plays as soon as it is drawn. Under the finished video: the quiz, the verification report, **Change it**
(`slow down step 4`, `explain step 2 for a beginner`), the transcript and the verified plan.

For frontend development, run `npm run dev` in `frontend/` (http://127.0.0.1:5173, which forwards `/api` to the
backend on port 8000).

Videos are saved in `outputs/<time>-<title>/`: `lesson_v1.mp4`, then `lesson_v2.mp4` after a change, and
the verified plan `lesson.json`.

## Tests

```bash
python -m pytest backend
```

The 35 tests cover every data structure, the verifier catching each kind of mistake (wrong state, false narration,
invented numbers, impossible operations, wrong quiz answers, too-short lessons), the planner's repair loop, rate
limits and the fallback model, and the revision flow (with a fake LLM, so no key is needed), plus two real clip
renders with sound. `python backend/scripts/live_eval.py --render` runs the same checks against the real API.

## Performance (AMD Ryzen 5 4500U laptop, 6 cores, CPU only, 3 drawing processes, draft quality)

A new 128-second stack lesson, from the moment the plan exists to the finished video, with a quiz call that takes
60 s (a typical free-tier reply; we measured 8 to 123 s). Each run starts from an empty cache.
`python backend/scripts/latency_benchmark.py --plan stack --quiz-seconds 60 --runs sequential,overlap --threads 0,2,4`

| Order | Voice threads | First scene playable | Finished video |
| --- | --- | ---: | ---: |
| Before: quiz first, then voice and drawing | default | 120 s, 127 s | 211 s, 182 s |
| After: quiz written during voice and drawing | default | 76 s, 58 s | 155 s, 136 s |
| After | 2 | 49 s | 122 s |
| After | 4 | 63 s | 120 s |

The default rows were run twice (the first pair while a download was running); runs on this laptop vary by about
20 s. Writing the quiz during the build saves 46 to 56 s, most of the quiz call, and the first scene can be watched
about twice as soon. Two or four voice threads may help a little while the drawing processes share the CPU, but
the difference is within the noise, so the default stays and `VOICE_THREADS` is there for slower machines.

The voice alone speaks at about twice real time (see docs/research/voice-models.md). Revisions redraw only the scenes that changed.

## Limitations

- Free-tier API keys allow only a few requests per minute. When the provider says "rate limited", the app waits
  (10, 20, then 30 seconds) and tries again before showing a message.

- Only the five structures above. Other topics (heaps, sorting, DFS) are refused with a message rather than
  explained badly.
- At most 7 items or nodes per lesson, so the picture stays readable.
- The narration check is rule-based: it catches wrong values and false top/front/head/root/size/current-node
  statements, but not every possible wrong sentence (for example a wrong explanation of *why*).
- BFS takes neighbours in alphabetical (or numeric) order; the narration and quiz follow the same rule.
