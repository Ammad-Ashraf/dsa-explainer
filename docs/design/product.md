# Product layout

What the DSA Explainer app looks like: its pages, the sections on each page, and where every feature lives.

- **Sections** are adapted from the information architecture of [visualizedsa.com](https://visualizedsa.com/), with
  its course funnel replaced by our own product: verified, narrated video lessons made on your machine.
- **Visual design** follows [design-system.md](design-system.md): white stage, leaf-green punctuation, rounded Nunito
  type, toy-key buttons with a 4px lower lip, flat rounded illustrations. The illustrations are original: a friendly
  geometric helper ("Node", a round character made of a tree node) and data-structure tokens (stack plates, queue
  tickets, tree nodes, graph pins). No names, characters or assets from the brand the reference describes.
- **Everything runs locally.** The browser talks to the local API at `127.0.0.1`; only the language model call
  leaves the machine, using the learner's own key.

## Navigation

A sparse fixed 72px header: wordmark at left; **Studio**, **Library**, **My lessons** in the middle; a settings cog and
a compact green **New lesson** action at right. A small provider pill shows which language model is connected (or
"No key: saved lessons only").

## Pages

### 1. Home `/`

| # | Section | Content |
| --- | --- | --- |
| 1 | Illustrated promise | Left: helper-and-tokens illustration. Right: 32px headline "Watch any data structure come alive, step by checked step." **Make a lesson** (primary) and **Browse the library** (secondary). |
| 2 | Category rail | One row of algorithm families with colourful emblems (Linear, Trees, Graphs, Sorting, Searching, Hashing, Dynamic programming), each linking to the filtered library. |
| 3 | Benefit chapters (alternating) | "every step is checked" (the verifier), "a voice that lives on your laptop" (local narration), "quiz yourself" (verified quiz), "change any part" (revisions re-render only what changed). |
| 4 | How it works (sky stage) | The six-stage pipeline (Plan, Verify, Quiz, Voice, Draw, Join) as a floating object field, with one line per stage. |
| 5 | Popular lessons | Three saved lessons: difficulty tag, complexity badge, one-line blurb, **Watch**. |
| 6 | FAQ | Ruled disclosure rows: Do I need an API key? What runs locally? Which providers work? How do you know a lesson is correct? How long does a video take? Is it free? |
| 7 | Green close + footer | "Ready to see it move?" with **Make a lesson**, a green valley illustration that flows into a five-column green footer (Product, Library, Learn, Project, Open source). |

### 2. Studio `/studio` (the main workspace)

The page where a lesson is made and watched.

- **Composer** (top, before a job starts): a large topic box with example chips, level (beginner / intermediate /
  advanced), video quality (draft / standard / high), and **Make my lesson**. Under it: "or start from a saved lesson"
  linking to the library.
- **Pipeline rail** (left column while a job runs): the six stages as a vertical stepper. Each stage shows its state
  (waiting, running, done, failed), its time, and its detail. Plan shows each attempt and **why the verifier sent it
  back**; Voice and Draw show per-scene progress; the current message streams under the active stage.
- **Stage** (right, large): the video player. While drawing, finished clips appear one by one, so watching can start
  before the whole video is joined. Under the player: **chapter strip** (intro, step 1..n, summary, quiz), each
  chapter showing its operation (`push(7)`).
- **After the video is ready**, tabs under the player:
  - **Quiz**: interactive multiple choice; the answer reveals the explanation and "checked by running the operations".
  - **Verified**: the verification report (checks passed, rejected attempts, timing per stage).
  - **Change it**: the revision box ("slow down step 4", "explain step 2 for a beginner"), with chapter chips for
    quick edits; shows which clips will be re-drawn.
  - **Transcript**: the narration per chapter, with captions.
  - **Plan**: the verified lesson plan JSON, downloadable.
- **Version strip**: v1, v2, ... of the lesson after revisions, each playable.

### 3. Library `/library`

- Header with a search box and **category filter chips** (from the rail) and difficulty filter.
- **Algorithm grid**: cards with emblem, name, category, difficulty tag, complexity badge, number of saved lessons.

### 4. Algorithm page `/library/:algorithm`

| # | Section | Content |
| --- | --- | --- |
| 1 | Header | Back to library; name; tags (difficulty, category, key requirement such as "sorted input"); one-paragraph description. |
| 2 | Saved lessons | Verified lessons for this algorithm (level, length, scenario); **Watch** renders locally without an API key. |
| 3 | Make your own | A topic box prefilled for this algorithm, plus **custom data** input and quick presets (small, already sorted, worst case, random), sent to the Studio. |
| 4 | Complexity | Time (best, average, worst) and space table. |
| 5 | How it works | Short explanation plus the pseudocode the animation highlights. |
| 6 | Operations | The operations the simulator supports and the facts the verifier can check (transparency about what is verified). |

### 5. My lessons `/lessons` and `/lessons/:id`

- History of lessons made on this machine: title, algorithm, level, length, versions, date; search and delete.
- `/lessons/:id` opens the same lesson view as the Studio's finished state.

### 6. Settings `/settings`

- **Language model**: provider presets (Gemini, OpenAI, Anthropic, Groq, OpenRouter, Ollama, custom
  OpenAI-compatible URL), key field (stored only on this machine, never shown again in full), model picker loaded
  from the provider, fallback model, **Test connection**.
- **Voice**: engine and voice, speed, a **Preview voice** button.
- **Video**: default quality, drawing processes.
- **Storage**: where lessons and models live, disk used, clear cache.

## Responsive behaviour

Desktop first (the Studio is a two-column workspace). Under 896px the pipeline rail collapses above the player as a
horizontal stepper; under 600px everything stacks, actions become full width, and the footer columns wrap.
