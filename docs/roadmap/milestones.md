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
| 1 | Local API server | 0 | **Done** |
| 2 | Bring-your-own-key, provider-independent LLM layer | 1 | **Done** |
| 5 | Algorithm plugin architecture, new algorithms, saved-plan library | 0 | **Done** |
| 3 | React frontend | 1, 2, 5 (registry) | **Done** |
| 6 | Richer, still-verified animations | 5 | **Done** |
| 4 | Voice research and pluggable voice engines | 0 | **Done** |
| 7 | Stronger verification and an evaluation harness | 5 | **Done** |
| 8 | Latency and responsiveness | 1, 3 | **Done** |
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

- [x] 1.1 Data folder and settings: `DSA_HOME`, `settings.json`, lessons index; `config` reads from them.
- [x] 1.2 Lesson store: list, read and delete lessons in `outputs/` (plan, report, quiz, versions, timings).
- [x] 1.3 Job runner: one worker thread, a queue, events per job (stage, progress, message, clip ready), cancellation.
- [x] 1.4 Pipeline reports structured events (stage names, per-scene progress, each finished clip) instead of only text.
- [x] 1.5 FastAPI app `dsa_explainer/api/`: lessons, jobs, Server-Sent Events, saved plans, revisions, video and clip
      files with range requests, health.
- [x] 1.6 `python -m dsa_explainer serve` command; API tests with a fake LLM.

## Milestone 2: Bring-your-own-key, provider-independent LLM layer

**Why.** `authoring/llm.py` keeps one client, one fallback flag and one JSON-mode flag in module globals built from
`.env`, so the process has exactly one key and one provider.

- [x] 2.1 `authoring/llm.py` `Client` per provider configuration (one OpenAI-compatible adapter covers every preset,
      Anthropic included, through its compatible endpoint; native adapters plug in at `Client`).
- [x] 2.2 Provider presets registry (base URL, models, key page, notes) for Gemini, OpenAI, Anthropic, Groq,
      OpenRouter, Ollama, LM Studio and custom URLs.
- [x] 2.3 `LLMSettings` passed through planner, quiz and reviser; rate-limit and fallback state per client; no globals.
- [x] 2.4 Structured output: JSON Schema from the Pydantic models, used where the provider supports it.
- [x] 2.5 Keys stored in `settings.json`, redacted in logs and errors; `.env` still the default.
- [x] 2.6 API: list presets, save settings, test a connection, list a provider's models. Tests with fake providers,
      including a no-key-leak test.

## Milestone 5: Algorithm plugin architecture, new algorithms, saved-plan library

**Why.** Adding one algorithm today touches the simulator file, two lookup tables, the drawers and their enter/exit
tables, the verifier's fixed fact words and the structure list hard-coded in the planner prompt.

- [x] 5.1 `algorithms/` registry: one simulator class per algorithm, grouped by family (`linear`, `trees`,
      `graphs`, `arrays`, `hashing`, `dp`), each carrying its metadata (title, category, difficulty, complexity,
      description, pseudocode, keywords, presets, fact words, view). Drawers are grouped by picture in
      `media/views/` (stack, queue, linked list, tree, heap, graph, array, buckets, table), since many algorithms
      share one. Planner, verifier, quiz, renderer and API read from the registry; the planner only sends the
      reference of the algorithms a topic names.
- [x] 5.2 Migrate stack, queue, linked list, BST and BFS (`graph` stays an alias of `bfs`) with no behaviour change.
- [x] 5.3 Property-based tests (Hypothesis) comparing every simulator with a reference implementation; they found
      two real bugs (selection sort on one value, a graph edge given twice), both fixed.
- [x] 5.4 Wave 1, arrays and sorting: array view (bars and cells, pointers, ranges); bubble, insertion, selection,
      merge, quick sort; linear and binary search; deque.
- [x] 5.5 Wave 2, trees and heaps: min-heap / priority queue (tree and array views), heap sort, tree traversals.
- [x] 5.6 Wave 3, graphs: depth-first search, Dijkstra, topological sort.
- [x] 5.7 Wave 4, hashing and dynamic programming: hash table (chaining), DP table (Fibonacci, coin change).
- [x] 5.8 Saved-plan library: one verified plan per algorithm (22), written by Claude in `scripts/author_plans.py`
      with provenance, and `scripts/generate_plans.py` to draft more with any provider. More levels per algorithm
      are added through that script and review.

## Milestone 3: React frontend

**Why.** Replace Gradio with the product in [product.md](../design/product.md).

- [x] 3.1 `frontend/` with Vite, React, TypeScript, React Router, TanStack Query. The API types are written by hand in
      `src/api.ts` (most replies are plain dictionaries, so generated types would be empty); the API tests guard the
      shapes.
- [x] 3.2 Design tokens and primitives from the design system (buttons with the lower lip, chips, tags, tabs, rules).
- [x] 3.3 Original illustration set (helper, data-structure tokens, valley, category emblems) as SVG components.
- [x] 3.4 Home page.
- [x] 3.5 Studio: composer, pipeline rail with live events, progressive clip player, chapters, quiz, verification,
      revisions, transcript, plan, versions.
- [x] 3.6 Library and algorithm pages.
- [x] 3.7 My lessons and settings (providers, keys, models, voice, video, storage).
- [x] 3.8 The backend serves the built frontend; one command opens the app; responsive and keyboard checks.
- [x] 3.9 Remove Gradio; update the README.

## Milestone 6: Richer, still-verified animations

**Why.** The clips showed the structure and nothing else: no running counts, no link to the algorithm's code, values
that swapped simply slid through each other, and the dark stage did not match the app.

- [x] 6.1 Simulators report verified detail for the video. Each algorithm names its facts strip (`STRIP`, labels in
      `FACT_LABELS`) and the pseudocode lines each operation runs (`OP_LINES`, refined by `code_lines()` from what the
      simulator actually did: binary search's left or right branch, bubble sort's early stop, the traversal order).
      Counts the simulators lacked were added (comparisons for insertion, selection, quick sort, BST and both
      searches; swaps for quick sort and heaps; nodes walked in a linked list; Dijkstra's improved nodes; the coin
      used) and tested against instrumented reference implementations. The verifier records both per scene
      (`Frame.lines`, `Frame.strip_before`, `Frame.strip_after`); nothing comes from the language model.
- [x] 6.2 Pseudocode card beside the picture, with the lines the step ran highlighted; the facts strip above the
      picture updates with every step and marks what changed in blue (`media/panels.py`). The library's algorithm
      page highlights the lines of the operation a learner picks, and marks the facts the strip shows.
- [x] 6.3 Arc moves: an opt-in `View.arc`; in the array and heap views a value that moves travels on an arc, so two
      values that swap visibly pass each other (sorting swaps, sift up and down). *Reworded:* pointer re-linking,
      sift paths and DP cell fills were already animated by the generic morph and the ordered path pulses, so the
      task kept only what was missing.
- [x] 6.4 Light video theme from the design tokens: white stage, charcoal type, leaf green for new and done, blue for
      the path, orange for the current element; Nunito is bundled (`media/fonts`, SIL OFL) and registered with
      Pango so every machine draws the same letters. The web player's screen is white to match. The intro title
      card and the summary end card stay; 1080p is the "high" quality. `RENDER_VERSION` 5 re-renders cached clips.
- [x] 6.5 Layout regression tests instead of image diffs: for every saved plan, the centre and size of every shape in
      the intro and each step (and the pseudocode card) are compared with approved JSON in
      `tests/golden/layouts/`; `DSA_UPDATE_GOLDEN=1` approves a change, and a rule test keeps pictures clear of the
      card and the caption. *Reworded from "key frames compared with approved images":* pixel diffs break on font
      hinting and encoder versions across platforms and do not say what moved; the layouts do.

## Milestone 4: Voice research and pluggable voice engines

**Why.** The voice was one module hard-wired to Kokoro, with no captions, no way to pick or hear a voice in the
app, and data-structure words read wrongly ("deque" as "de-queue").

- [x] 4.1 Research document [docs/research/voice-models.md](../research/voice-models.md): eleven candidates with the
      licences of their code and weights, CPU speed (Kokoro measured here by thread count, RTF 0.48 on four cores
      of a Ryzen 5 4500U; Piper and Kitten TTS measured in a separate environment), timestamps and Windows support.
      Decision: Kokoro-82M stays the default. Records the licence position: `kokoro-onnx` phonemises through
      `phonemizer` (GPL-3.0+) and espeak-ng (GPL-3.0), installed as dependencies, and the path to a non-GPL
      phonemiser (`misaki` with `is_phonemes`).
- [x] 4.2 `media/voices/` engine interface (`Engine`: `voices()`, `synthesize()`), Kokoro as the first engine
      (ONNX Runtime session with configurable threads and execution providers); `media/voice.py` is gone.
- [x] 4.3 Timings and captions. *Reworded from "word timings":* no CPU engine we found exposes word timestamps, and
      the released Kokoro ONNX file has no duration output, so each sentence is synthesised on its own and joined
      with a 0.25 s pause; sentence times are exact, long sentences are split into caption-sized pieces at commas.
      Every lesson version gets a WebVTT file (`lesson_v<n>.vtt`, served at `/api/lessons/{id}/captions/{v}`), the
      lesson player shows it as a captions track, and the progressive player builds one per clip from the clip
      event's cues.
- [x] 4.4 Pronunciation lexicon `media/voices/lexicon.py` (notation such as O(n log n), a[i], push(7), ->, <=;
      acronyms; deque, enqueue, Dijkstra), applied to what is spoken only, versioned in the audio cache key, with
      tests.
- [x] 4.5 Voices in the API and the app: `GET /api/voices` (engines, licences, readiness, voices),
      `POST /api/voices/preview` (a cached WAV sample), and settings `voice_engine`, `voice`, `voice_speed`. The
      Settings page has an engine and voice picker grouped by accent, a speed slider and a **Preview voice** button.

## Milestone 7: Stronger verification and an evaluation harness

**Why.** Two gaps were found while writing the saved plans (below), the quiz's wrong options were whatever the
model wrote, and there was no measure of how much the verifier actually catches.

- [x] 7.1 Declared claims: a scene may list `claims` (`{"fact", "value", "when": "before" | "after"}`); each is
      checked exactly at its moment and the narration must say the value; the planner prompt asks for them. The
      pattern checks stay as the backstop and now hold a step's statements to the state *right after* it unless a
      claim declares "before". Numbers must be values, arguments or the simulator's own counts at that moment.
      Both gaps are closed and tested: "the root is 3" on the step that changes the root, and "D drops to 7"
      passing as a count.
- [x] 7.2 Paraphrase coverage: "holds three values", "has four items", "only two nodes remain", "7 is now the top",
      "becomes the new root", "changes to", "drops to", "the distance to D", "D's distance", "after three
      comparisons", and sentences that are not claims ("this is the root of the problem"), with tests.
- [x] 7.3 Quiz: wrong options from simulated mistakes (`authoring/mistakes.py`: forgetting the last operation,
      running it twice, the wrong order, the value before any operation, treating a queue as a stack, BFS as DFS,
      one sort as another), each verified wrong and kept with its reason, which the app shows when a learner picks
      it. New question types: true/false (`claim`) and counts (comparisons, swaps, shifts, nodes walked). A
      question with a right answer but broken options is repaired instead of thrown away, and built-in questions
      cover every algorithm when the model fails.
- [x] 7.4 Mutation testing over every saved plan (`core/mutants.py`, `scripts/mutation_report.py`,
      `tests/test_mutations.py`): 601 mutants of ten kinds, **97.0% caught** (92.7% by the Milestone 6 verifier);
      wrong facts in the narration went from 78% to 100%. The survivors and why they survive are in
      [docs/research/verification.md](../research/verification.md).
- [x] 7.5 Evaluation harness `scripts/eval_harness.py`: algorithms x providers x JSON modes, timing of every
      language-model call, a call budget for free tiers, JSON-lines results and a Markdown summary; `--dry-run`
      replays the saved plans so the harness is tested offline. `live_eval.py` stays as the fixed course run.
      Results of a real Gemini run by JSON mode: [docs/research/eval-json-modes.md](../research/eval-json-modes.md).

## Milestone 8: Latency and responsiveness

**Why.** A new lesson waited for the quiz call (one to two minutes on a free tier) before the first scene was even
voiced, and the app showed stage times only for stages that had finished.

- [x] 8.1 Per-stage timings: the reporter records every stage's duration and when it started; each lesson version
      saves them (`meta.json` `timings.stages`, `timings.spans`, `timings.total`). The pipeline rail shows a live
      timer on the running stage, and the Verified tab draws "Where the time went": one bar per stage on a shared
      clock, so the quiz overlapping the drawing is visible.
- [x] 8.2 The quiz is written in a background thread (with the job's language-model settings) while the scenes are
      voiced and drawn; `build_video` adds the quiz clips last, when the questions are ready, and keeps announcing
      finished clips while it waits. A failed or empty quiz falls back to built-in questions, as before.
- [x] 8.3 Progressive playback: clips are announced as soon as they are drawn, even while later scenes are still
      being voiced, and the Studio plays them in order.
- [x] 8.4 Voice speed: ONNX Runtime threads (`VOICE_THREADS`) and execution providers (`VOICE_PROVIDERS`, for
      example DirectML or CUDA, with the CPU as the fallback) are configurable; measured by thread count in
      [docs/research/voice-models.md](../research/voice-models.md). The default (one thread per core) is within 6%
      of the best setting, so it stays.
- [x] 8.5 Before and after measurements (`scripts/latency_benchmark.py`, in the README):

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

## Milestone 9: Open-source release

- [ ] 9.1 `LICENSE` (MIT) and `THIRD_PARTY_NOTICES.md`.
- [ ] 9.2 Packaging: `pyproject.toml` metadata, `dsa-explainer` command, models downloaded on first run, built
      frontend bundled.
- [ ] 9.3 GitHub Actions on Windows, macOS and Linux: backend tests, `ruff`, frontend build and tests.
- [ ] 9.4 `CONTRIBUTING.md` with an "add an algorithm" guide, code of conduct, issue and pull-request templates.
- [ ] 9.5 README rewritten for the open-source project; course material linked from it.
