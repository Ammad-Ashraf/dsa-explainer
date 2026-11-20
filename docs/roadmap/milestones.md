# Milestones

How the ideas in [vision.md](vision.md) become work. Each milestone says why it exists, then lists its tasks; a
task is ticked when it is committed on `feat/open-source-platform`. Code paths are inside `backend/dsa_explainer/`.
The product the milestones build is described in [../design/product.md](../design/product.md).

## Rules for every milestone

- **The verifier invariant is never relaxed.** The language model never has the last word on facts; the renderer
  draws only the verifier's snapshots of the real simulation. New features add checks, never remove them.
- **Tests stay green and the app keeps running** after every commit. Each task adds tests for what it adds.
- All work lands on `feat/open-source-platform` in meaningful commits. `main` stays as the course submission.

## Decisions

The open questions from the vision, decided so work can proceed without waiting:

| Question | Decision | Why |
| --- | --- | --- |
| Layout reference | [visualizedsa.com](https://visualizedsa.com/) sections, adapted in [product.md](../design/product.md) | Shared by Ammad. Its course upsell is replaced by our own lesson workflow. |
| Design reference | [design-system.md](../design/design-system.md) | Shared by Ammad. Applied with original illustrations; no third-party brand assets. |
| Licence | **MIT** for our code, with `THIRD_PARTY_NOTICES.md` listing dependency and model licences | Simple and permissive. espeak-ng (GPL-3.0) is a separately installed dependency of the phonemizer, not code we ship; Milestone 4 records this and keeps a path to a non-GPL phonemiser. |
| Name | Keep **DSA Explainer** (package `dsa_explainer`, command `dsa-explainer`) | Already in the report, the code and the course submission. |
| Who writes the saved plans | Claude writes them in the development session, and the **verifier must accept every one** before it is committed; `scripts/generate_plans.py` lets anyone regenerate them with their own provider | No paid key is needed, and correctness does not depend on who wrote the plan. |
| Where keys and lessons live | A data folder: the repository root when run from source (as today), `~/.dsa-explainer` when installed; overridable with `DSA_HOME`. Keys go in `settings.json` there, outside git, never logged | One rule for both ways of running, and existing `models/`, `outputs/`, `cache/` keep working. |
| Gradio | Kept until the React app reaches parity, then removed (end of Milestone 3) | The app keeps working at every commit. |
| Course submission | `main` is untouched; this branch is merged only when Ammad decides | The submission must not change under the graders. |

## Overview and order of work

| # | Milestone | Depends on | Status |
| --- | --- | --- | --- |
| 0 | Reorganise the repository and write the roadmap | | **Done** |
| 1 | Local API server | 0 | Next |
| 2 | Bring-your-own-key, provider-independent LLM layer | 1 | |
| 5 | Algorithm plugin architecture, new algorithms, saved-plan library | 0 | |
| 3 | React frontend | 1, 2, 5 (registry) | |
| 6 | Richer, still-verified animations | 5 | |
| 4 | Voice research and pluggable voice engines | 0 | |
| 7 | Stronger verification and an evaluation harness | 5 | |
| 8 | Latency and responsiveness | 1, 3 | |
| 9 | Open-source release | all | |

Milestone numbers are names, not order: the table is in the order the work happens. Milestone 5's registry comes
before the frontend because the library pages are built from it.

---

## Milestone 0: Reorganise the repository and write the roadmap (done)

- [x] Monorepo layout: `backend/` now, `frontend/` in Milestone 3; package grouped by stage (`core/`, `authoring/`,
      `media/`); saved plans in `dsa_explainer/plans/`; course documents in `docs/course/`.
- [x] Anchor `.gitignore` patterns so runtime folders never hide source folders.
- [x] Vision, milestones, product layout and design reference in `docs/`.

## Milestone 1: Local API server

**Why.** The React app needs an HTTP API; today the pipeline is called directly from Gradio callbacks.

- [ ] 1.1 Data folder and settings: `DSA_HOME`, `settings.json`, lessons index; `config` reads from them.
- [ ] 1.2 Lesson store: list, read and delete lessons in `outputs/` (plan, report, quiz, versions, timings).
- [ ] 1.3 Job runner: one worker thread, a queue, events per job (stage, progress, message, clip ready), cancellation.
- [ ] 1.4 Pipeline reports structured events (stage names, per-scene progress, each finished clip) instead of only text.
- [ ] 1.5 FastAPI app `dsa_explainer/api/`: lessons, jobs, Server-Sent Events, saved plans, revisions, video and clip
      files with range requests, health.
- [ ] 1.6 `python -m dsa_explainer serve` command; API tests with a fake LLM.

## Milestone 2: Bring-your-own-key, provider-independent LLM layer

**Why.** `authoring/llm.py` keeps one client, one fallback flag and one JSON-mode flag in module globals built from
`.env`, so the process has exactly one key and one provider.

- [ ] 2.1 `authoring/providers/`: `LLMProvider` interface, OpenAI-compatible adapter, native Anthropic adapter.
- [ ] 2.2 Provider presets registry (base URL, models, key page, notes) for Gemini, OpenAI, Anthropic, Groq,
      OpenRouter, Ollama, LM Studio and custom URLs.
- [ ] 2.3 `LLMSettings` passed through planner, quiz and reviser; rate-limit and fallback state per client; no globals.
- [ ] 2.4 Structured output: JSON Schema from the Pydantic models, used where the provider supports it.
- [ ] 2.5 Keys stored in `settings.json`, redacted in logs and errors; `.env` still the default.
- [ ] 2.6 API: list presets, save settings, test a connection, list a provider's models. Tests with fake providers,
      including a no-key-leak test.

## Milestone 5: Algorithm plugin architecture, new algorithms, saved-plan library

**Why.** Adding one algorithm today touches the simulator file, two lookup tables, the drawers and their enter/exit
tables, the verifier's fixed fact words and the structure list hard-coded in the planner prompt.

- [ ] 5.1 `algorithms/` registry: one package per algorithm with simulator, drawer and metadata (name, category,
      difficulty, complexity, description, pseudocode, fact words, presets). Planner, verifier, renderer, quiz and
      API read from it.
- [ ] 5.2 Migrate stack, queue, linked list, BST and BFS with no behaviour change (all tests, same pictures).
- [ ] 5.3 Property-based tests (Hypothesis) comparing every simulator with a reference implementation.
- [ ] 5.4 Wave 1, arrays and sorting: array (sequence) renderer; bubble, insertion, selection, merge, quick sort;
      linear and binary search; deque.
- [ ] 5.5 Wave 2, trees and heaps: min-heap / priority queue (tree and array views), heap sort, tree traversals.
- [ ] 5.6 Wave 3, graphs: depth-first search, Dijkstra, topological sort.
- [ ] 5.7 Wave 4, hashing and dynamic programming: hash table (chaining), DP table (Fibonacci, coin change).
- [ ] 5.8 Saved-plan library: verified plans for every algorithm at several levels, with provenance, plus
      `scripts/generate_plans.py`.

## Milestone 3: React frontend

**Why.** Replace Gradio with the product in [product.md](../design/product.md).

- [ ] 3.1 `frontend/` with Vite, React, TypeScript, React Router, TanStack Query; API types generated from OpenAPI.
- [ ] 3.2 Design tokens and primitives from the design system (buttons with the lower lip, chips, tags, tabs, rules).
- [ ] 3.3 Original illustration set (helper, data-structure tokens, valley, category emblems) as SVG components.
- [ ] 3.4 Home page.
- [ ] 3.5 Studio: composer, pipeline rail with live events, progressive clip player, chapters, quiz, verification,
      revisions, transcript, plan, versions.
- [ ] 3.6 Library and algorithm pages.
- [ ] 3.7 My lessons and settings (providers, keys, models, voice, video, storage).
- [ ] 3.8 The backend serves the built frontend; one command opens the app; responsive and keyboard checks.
- [ ] 3.9 Remove Gradio; update the README.

## Milestone 6: Richer, still-verified animations

- [ ] 6.1 Simulators report verified detail: comparisons, swaps, pointer variables, pseudocode line.
- [ ] 6.2 Pseudocode panel in the video, highlighted from the simulator.
- [ ] 6.3 Operation-specific animations: swap arcs, pointer re-linking, sift paths, sorting bars, DP cell fills.
- [ ] 6.4 Video theme from the design tokens (light stage, green accents, rounded type); title and end cards; 1080p.
- [ ] 6.5 Visual regression tests: key frames of saved plans compared with approved images.

## Milestone 4: Voice research and pluggable voice engines

- [ ] 4.1 Research document `docs/research/voice-models.md`: candidates, licences, CPU speed, quality, timestamps.
- [ ] 4.2 `media/voices/` engine interface; Kokoro as the first engine.
- [ ] 4.3 Word timings (from the engine, or by alignment) feeding captions (WebVTT).
- [ ] 4.4 Pronunciation lexicon for data-structure terms, with tests.
- [ ] 4.5 Voice preview and engine selection in the API and settings.

## Milestone 7: Stronger verification and an evaluation harness

- [ ] 7.1 Declared claims: each scene lists the facts it states; the verifier checks each one and that the narration
      expresses it; the regular expressions remain a backstop.
- [ ] 7.2 Paraphrase coverage for the narration checker (counts, "holds", "sits on top"), with tests.
- [ ] 7.3 Quiz: new question types and distractors from simulated mistakes, verified wrong.
- [ ] 7.4 Mutation testing of the verifier over every saved plan, with a reported catch rate.
- [ ] 7.5 Evaluation harness extending `scripts/live_eval.py` across algorithms and providers.

## Milestone 8: Latency and responsiveness

- [ ] 8.1 Per-stage timings recorded for every job and shown in the app.
- [ ] 8.2 Write the quiz while lesson scenes are voiced and drawn.
- [ ] 8.3 Progressive playback of finished clips (already used by the Studio player).
- [ ] 8.4 Voice speed: ONNX Runtime thread tuning, optional GPU execution providers.
- [ ] 8.5 Before and after measurements in the README.

## Milestone 9: Open-source release

- [ ] 9.1 `LICENSE` (MIT) and `THIRD_PARTY_NOTICES.md`.
- [ ] 9.2 Packaging: `pyproject.toml` metadata, `dsa-explainer` command, models downloaded on first run, built
      frontend bundled.
- [ ] 9.3 GitHub Actions on Windows, macOS and Linux: backend tests, `ruff`, frontend build and tests.
- [ ] 9.4 `CONTRIBUTING.md` with an "add an algorithm" guide, code of conduct, issue and pull-request templates.
- [ ] 9.5 README rewritten for the open-source project; course material linked from it.
