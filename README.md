# DSA Explainer

[![CI](https://github.com/Ahmed-Javaid/NLP-Project-2026/actions/workflows/ci.yml/badge.svg)](https://github.com/Ahmed-Javaid/NLP-Project-2026/actions/workflows/ci.yml)
[![Licence: MIT](https://img.shields.io/badge/licence-MIT-58cc02.svg)](LICENSE)

**Watch any data structure come alive, step by checked step.** Type a topic such as *"how does a queue handle
print jobs"* or *"Dijkstra from A on this graph"*. DSA Explainer plans a lesson with the language model of your
choice, **runs every step on a real simulator** so nothing false reaches the screen, narrates it with a voice
model **on your own computer**, animates it with Manim, and ends with a quiz whose answers were computed, not
guessed. Ask for *"slow down step 4"* and only that scene is redrawn.

- **Verified, not generated.** The language model writes a plan; a verifier runs it on 22 real simulators and
  checks every predicted state, every fact the narration states and every quiz answer. It catches 97% of planted
  mistakes across 601 mutants of the saved lessons ([how we measure](docs/research/verification.md)).
- **Local first.** The voice (Kokoro-82M), the animation and the video all run on your machine. Only the planning
  call leaves it, with your own key for any provider (Gemini, OpenAI, Anthropic, Groq, OpenRouter) or none at all
  with a local Ollama or LM Studio model. The 22 saved lessons need no key.
- **22 algorithms** in seven families: stack, queue, deque, linked list; binary search tree, tree traversals,
  min-heap; BFS, DFS, Dijkstra, topological sort; bubble, insertion, selection, merge, quick and heap sort; linear
  and binary search; hash table; Fibonacci and coin change.
- **Videos that teach.** Beside the structure: the pseudocode with the lines each step ran highlighted, and a strip
  of the simulator's facts (comparisons, swaps, the pivot, distances). Values that swap pass each other on arcs.
  Captions come with every video.
- **A quiz from real mistakes.** Wrong options are what you get by forgetting a step, doing two in the wrong order
  or treating a queue as a stack; the app tells you which mistake you made.

> This project began as the Natural Language Processing course project of Ahmed Javaid and Ammad Ashraf (Fall
> 2026). The submitted course version lives on the `main` branch and is documented in [docs/course/](docs/course/).

## Quick start

You need **Python 3.11 to 3.13** and about 1 GB of disk. On Linux, first install Cairo and Pango for Manim
(`sudo apt-get install libcairo2-dev libpango1.0-dev pkg-config ffmpeg`); on macOS, `brew install cairo pango
pkg-config`.

```bash
git clone https://github.com/Ahmed-Javaid/NLP-Project-2026.git dsa-explainer
cd dsa-explainer
python -m venv .venv
.venv/Scripts/activate                       # macOS and Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -e . --no-deps
cd frontend && npm ci && npm run build && cd ..   # the web app (Node 20 or newer)
dsa-explainer
```

`dsa-explainer` downloads the voice model on first run (about 350 MB), starts the app at http://127.0.0.1:8000 and
opens it. Lessons from the **Library** play straight away. To make lessons from your own topics, open **Settings**,
pick a provider and paste a key (Gemini and Groq have free tiers; Ollama needs no key). A `.env` file works too:
copy `.env.example`.

Other commands: `dsa-explainer serve --port 8001`, `dsa-explainer download-models`,
`dsa-explainer "how does a stack work" --level beginner` (makes a video from the terminal), `dsa-explainer --version`.

A wheel that bundles the web app is built in CI (`pip install dsa_explainer-*.whl`, then `dsa-explainer`); its
data folder is `~/.dsa-explainer` (set `DSA_HOME` to move it).

## How it works

![DSA Explainer architecture](docs/course/architecture.png)

**The language model never has the last word on facts, and the renderer draws only the verifier's snapshots of the
real simulation.**

| Stage | What happens | Code (in `backend/dsa_explainer/`) |
| --- | --- | --- |
| Plan | The model writes a JSON plan: initial data, one operation per step (`push(7)`), the state it expects after each, narration, and the facts the narration claims | `authoring/planner.py` |
| Verify | Every step runs on the simulator; wrong states, false claims, invented numbers and impossible operations send the plan back with the truth, up to four attempts. No correct plan, no video | `core/verifier.py`, `algorithms/` |
| Quiz | Written by the model while the video is made; every answer recomputed, wrong options from simulated mistakes | `authoring/quiz.py`, `authoring/mistakes.py` |
| Voice | Each sentence spoken locally, so caption timings are exact; a lexicon fixes "deque", "BFS", "O(n log n)" | `media/voices/` |
| Draw | One Manim clip per scene from the verifier's snapshots, several at once, cached by content | `media/render.py`, `media/views/`, `media/panels.py` |
| Join | ffmpeg joins the clips; captions become one WebVTT file | `media/video.py` |

The React app (`frontend/`) follows the job live over Server-Sent Events and plays each scene as soon as it is
drawn. Design notes: [product](docs/design/product.md), [design system](docs/design/design-system.md),
[voice research](docs/research/voice-models.md), [verification](docs/research/verification.md),
[roadmap](docs/roadmap/milestones.md).

## Performance

Measured on an AMD Ryzen 5 4500U laptop (6 cores, no GPU), Windows 11, 3 drawing processes, draft quality.

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

- **The voice** speaks about twice as fast as real time (real-time factor 0.48 with 4 ONNX Runtime threads, 0.51
  with the default, 1.04 with one thread). `VOICE_THREADS` sets the threads; `VOICE_PROVIDERS` can name a GPU
  execution provider (`DmlExecutionProvider` with `onnxruntime-directml` on Windows, `CUDAExecutionProvider` with
  `onnxruntime-gpu`), with the CPU as the fallback. Reproduce: `python backend/scripts/voice_benchmark.py`.
- **The language model** dominates a new lesson: on Gemini's free tier a plan call took 6 to 57 s and a quiz call 8
  to 123 s ([measurements](docs/research/eval-json-modes.md)). The quiz is now written while the scenes are voiced
  and drawn, so its time overlaps the build instead of adding to it, and the first scene plays long before the
  video is finished.
- **Revisions** redraw only the scenes that changed; every other clip comes from the cache.

## Development

```bash
python -m pytest backend -q                 # the backend suite (tests that need the voice model skip without it)
ruff check .
cd frontend && npm test && npm run build    # unit tests; type check, lint and build
python backend/scripts/mutation_report.py   # how many planted mistakes the verifier catches
python backend/scripts/eval_harness.py --dry-run   # the evaluation harness, offline
```

CI runs the backend on Windows, macOS and Linux, the web app's tests and build, and builds a wheel with the web app
inside. [CONTRIBUTING.md](CONTRIBUTING.md) explains how to add an algorithm, a voice engine or a provider.

```
backend/dsa_explainer/
  algorithms/   22 simulators, grouped by family, with their catalogue data, facts strip and pseudocode lines
  core/         lesson schema, verifier, mutation testing (no AI, no I/O)
  authoring/    what a language model writes: planner, quiz, simulated mistakes, revisions, providers
  media/        voices (engines, lexicon, captions), views and panels (Manim), joining
  api/          FastAPI app and job runner (live progress over Server-Sent Events)
  plans/        22 verified saved lessons
backend/scripts/  model download, benchmarks, evaluation harness, mutation report, plan authoring
backend/tests/    unit, property-based (Hypothesis), golden layout and mutation tests
frontend/         React + TypeScript web app (Vite), served by the backend once built
docs/             roadmap, design, research, and the course submission
```

## Limitations

- At most 7 to 8 items or nodes per lesson, so pictures stay readable; lessons are in English.
- The narration check reads facts it can recognise (and every fact a plan declares); it cannot judge an explanation
  of *why*. The [verification note](docs/research/verification.md) lists what still gets through.
- Free-tier keys allow few requests a day; the app waits on rate limits and switches to a fallback model.

## Licence

MIT, see [LICENSE](LICENSE). Models, fonts and dependencies keep their own licences, listed in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md); note that the voice's phonemiser (espeak-ng through `phonemizer`)
is GPL-3.0, installed as a dependency.

## The course project

DSA Explainer was built for Project 1 (Data Structure Explainer) of our NLP course; Ahmed Javaid implemented the
course version. The course documents describe the version on `main`: the [report](docs/course/report.md)
([PDF](docs/course/report.pdf)), the [architecture diagram](docs/course/architecture.png), the
[live evaluation](docs/course/live-eval.md), the [Loom video guide](docs/course/loom-video-guide.md), the
[AI prompts](docs/course/ai-prompts.md) and the [submission checklist](docs/course/submission-checklist.md).
