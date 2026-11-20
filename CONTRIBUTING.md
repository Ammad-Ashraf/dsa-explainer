# Contributing to DSA Explainer

Thank you for helping. DSA Explainer turns a data-structures topic into a narrated, animated lesson made on the
learner's own computer, and it promises one thing above all: **every fact in a video is checked by running a real
simulation**. Contributions are welcome as long as they keep that promise.

By taking part you agree to follow the [code of conduct](CODE_OF_CONDUCT.md). Contributions are accepted under the
project's [MIT licence](LICENSE).

## The one rule

**The language model never has the last word on facts, and the renderer only draws the verifier's snapshots of the
real simulation.** New features add checks; they never remove them. If a change would let something reach a
video without being verified, it will not be merged, however nice it looks.

## Set up

You need Python 3.11 to 3.13, Node 20 or newer, and about 1 GB of disk for the voice model and the cache.

```bash
git clone https://github.com/Ahmed-Javaid/NLP-Project-2026.git dsa-explainer
cd dsa-explainer
python -m venv .venv
.venv/Scripts/activate            # Windows; on macOS and Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -e . --no-deps        # the `dsa-explainer` command, pointing at your checkout
pip install ruff
python backend/scripts/download_models.py
cd frontend && npm ci && npm run build && cd ..
cd backend && python -m dsa_explainer serve --open
```

On Linux, Manim needs Cairo and Pango first: `sudo apt-get install libcairo2-dev libpango1.0-dev pkg-config ffmpeg`.
On macOS: `brew install cairo pango pkg-config`.

While working on the web app, run `npm run dev` in `frontend/` (it proxies `/api` to the backend on port 8000).

## Before you open a pull request

```bash
python -m pytest backend -q        # about two minutes; tests that need the voice model skip without it
ruff check .
cd frontend && npm test && npm run build   # build = type check + ESLint + Vite
```

- Every change comes with tests for what it adds. Bugs get a test that fails before the fix.
- If you change how a picture is laid out, the golden layouts will fail on purpose. Look at a few frames, then
  approve the new layouts with `DSA_UPDATE_GOLDEN=1 python -m pytest backend/tests/test_layouts.py` and commit the
  JSON diff with your change.
- If you change a view or the renderer, bump `RENDER_VERSION` in `media/render.py` so cached clips are redrawn.
- Keep the verifier's mutation catch rate where it is or higher (`python backend/scripts/mutation_report.py`).
- Write for the reader: short sentences in docs, comments that say why, names that say what.

## Add an algorithm

Everything the app knows about an algorithm lives in one simulator class. The planner's prompt, the verifier, the
quiz, the renderer, the facts strip, the pseudocode highlights and the library pages all read from it. As an
example, here is how you would add *selection of the k-th smallest value with a min-heap*; follow the steps for
your own algorithm.

### 1. Write the simulator

Put it in the module of its family in `backend/dsa_explainer/algorithms/` (`linear`, `trees`, `graphs`,
`arrays`, `hashing`, `dp`), or a new module. Subclass `Structure` (or a family base such as `_Sort` or `_Graph`)
and fill in the catalogue and the simulation:

```python
class KthSmallest(_ArrayHeap):
    NAME, TITLE = "kth_smallest", "K-th smallest (with a heap)"
    CATEGORY, DIFFICULTY, VIEW = "trees", "intermediate", "heap"
    SUMMARY = "Pop the minimum k times: the last value popped is the k-th smallest."
    DESCRIPTION = "..."                                  # one paragraph for the library page
    COMPLEXITY = {"best": "O(n)", "average": "O(n + k log n)", "worst": "O(n + k log n)", "space": "O(n)"}
    PSEUDOCODE = ("heapify the values", "repeat k times: x = extract_min()", "return x")
    KEYWORDS = ("k-th smallest", "kth smallest", "order statistic")
    PRESETS = {"k = 3": {"values": [7, 2, 9, 4, 1], "k": 3}, "k = 1": {"values": [5, 3, 8], "k": 1}}
    OPS = {"pop_min": ()}                                # the only operations a plan may use
    FACTS = ("popped", "root", "size", "items", "swaps")
    STRIP = ("popped", "root", "size", "swaps")          # the facts strip beside the picture
    OP_LINES = {"pop_min": (1,)}                         # pseudocode lines each operation runs
    HELP = "kth_smallest: initial = {...}. ops: pop_min() .... state = .... facts: ...."

    def op_pop_min(self):
        ...                                              # do it for real; raise OpError when impossible
        return [ids, of, elements, to, highlight]        # in the order the animation should visit them

    def state(self): ...                                 # what the planner must predict, plain JSON
    def facts(self): ...                                 # every fact name in FACTS -> its current value
    def snapshot(self): ...                              # what the view draws, with a stable id per element
```

Rules that keep the verifier honest:

- `run()` must change nothing when it raises `OpError`.
- Element ids from `self.new_id()` stay with their value for life, so the morph can animate moves.
- Everything in `STRIP` must be in `FACTS`; `code_lines()` may refine `OP_LINES` from what the operation
  actually did (see `BinarySearch.code_lines`).
- `HELP` is all the planner knows about your algorithm: state the data format, every operation, the state format
  and every fact, precisely.

### 2. Register it

Add the class to `ALL` in `backend/dsa_explainer/algorithms/__init__.py`. If the narration uses a word for one of
its facts that is not a fact name ("pivot", "middle"), add it to `FACT_WORDS` so the verifier checks it.

### 3. Give it a picture

If an existing view draws its snapshot (`stack`, `queue`, `linked_list`, `tree`, `heap`, `graph`, `array`,
`buckets`, `table`), name it in `VIEW` and you are done. Otherwise add a `View` subclass in
`backend/dsa_explainer/media/views/` that returns `{stable key: shape}`, register it in `views/__init__.py`, and
set `arc` if values that move should travel on an arc. Draw for the whole 14.2 x 8 frame; the renderer scales the
picture next to the pseudocode card.

### 4. Test it

- In `backend/tests/test_algorithms.py`, compare the simulator with an independent reference implementation on
  random inputs with Hypothesis (see the existing tests: they found real bugs).
- `test_views.py`, `test_algorithms.py::test_every_algorithm_is_fully_described` and
  `test_strip_and_pseudocode_lines_come_from_the_simulator` pick up every registered algorithm automatically.

### 5. Add a saved lesson

Write a plan spec in `backend/scripts/author_plans.py` (data, steps, narration, quiz) and run
`python backend/scripts/author_plans.py kth_smallest`. The script fills in every claimed state from the simulator
and writes the plan only if the verifier accepts it. Then approve its golden layout
(`DSA_UPDATE_GOLDEN=1 python -m pytest backend/tests/test_layouts.py -k kth_smallest`), render it once with
`python -m dsa_explainer --file dsa_explainer/plans/kth_smallest.json` (inside `backend/`) and watch it.

## Add a voice engine

Subclass `Engine` in `backend/dsa_explainer/media/voices/` (`ready()`, `voices()`, `synthesize(sentence, voice,
speed)`), add it to `ENGINES`, and document its licence in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and
[docs/research/voice-models.md](docs/research/voice-models.md). The lexicon, sentence timings, captions and caching
are shared, so an engine stays small. Keep heavy imports inside the engine so the app starts without them.

## Add a language-model provider

Most providers speak the OpenAI chat API: add a preset to `backend/dsa_explainer/authoring/providers.py`. A
provider that does not can get its own adapter behind `llm.Client`. Never log or return an API key; the tests
check this.

## Reporting bugs and ideas

Use the issue templates. For a wrong video, attach the lesson's plan (Plan tab, *Download plan*): a wrong fact
that got past the verifier is the most valuable bug report this project can get.
