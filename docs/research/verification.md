# How well does the verifier catch mistakes?

*Milestone 7, November 2026. Every number here is produced by a script in the repository.*

The verifier is the reason DSA Explainer can let a language model write lessons: the model never has the last word
on facts. This note measures how good that last word is, and records what Milestone 7 changed.

## What the verifier checks

For every scene of a plan it runs the step on the real simulator, then checks:

1. the operation is possible (no `pop` on an empty stack);
2. the plan's `claimed_state` equals the true state after the step;
3. **declared claims** (new): a scene may list the facts its narration states, each marked as true *before* or
   *after* the step, for example `{"fact": "root", "value": 3, "when": "before"}`. Each one must be exactly true at
   that moment, and the narration must actually say the value;
4. the narration's own statements, found by patterns (*"the top is now 7"*, *"5 sits at the front"*, *"the stack
   holds three values"*, *"D drops to 8"*, *"after three comparisons"*), must be true **right after** the step
   (or before it, when a declared claim says so);
5. every number in the narration must be a value of the structure, an argument of the operation, or one of the
   simulator's own counts at that moment (comparisons, swaps, size, indices, distances);
6. every quiz answer is recomputed by running the question's operations; wrong options carry the simulated mistake
   that produces them, and that is checked too.

## Two gaps found while writing the saved plans, now closed

| Gap | Example that used to pass | Now |
| --- | --- | --- |
| A fact true either before *or* after the step was accepted | *"The root is 1"* on the `extract_min()` step that removes 1 | Rejected: *"which was true before this step; right after it the root is 3. Say it in the past tense, or declare it with `when: before`"* |
| Any number from 0 to 8 passed as a "count" | *"D drops to 7"* when Dijkstra gives 8 | Rejected twice over: *"drops to"* is now read as a distance claim, and 7 is not a value, an argument or a count of the structure |

Both are regression tests in `backend/tests/test_verifier.py`.

## Mutation testing

`python backend/scripts/mutation_report.py` plants one mistake at a time in each of the 22 saved plans, in ten
ways, and runs the verifier on every mutant. A mutant is *caught* when the verifier reports an error. Mutants that
teach exactly the same thing as the original (dropping a read-only `peek`, or a quiz operation that does not change
the answer) are not counted, because accepting them is correct.

| Mistake planted | Mutants | Milestone 6 verifier | Milestone 7 verifier |
| --- | ---: | ---: | ---: |
| wrong `claimed_state` | 111 | 100% | 100% |
| step that changes the state dropped | 83 | 98% | 98% |
| wrong quiz answer | 44 | 100% | 100% |
| quiz operation dropped | 37 | 100% | 100% |
| wrong fact in the narration | 36 | 78% | **100%** |
| invented number in the narration | 115 | 100% | 100% |
| every number in a step shifted by one | 95 | 67% | **86%** |
| changed initial data | 20 | 95% | 95% |
| changed operation argument | 29 | 93% | 93% |
| two operations swapped | 31 | 100% | 100% |
| **all** | **601** | **92.7%** | **97.0%** |

`backend/tests/test_mutations.py` keeps the six "always caught" rows at 100% and the overall rate at or above
96.5%, so the rate can only go up.

### What still gets through, and why

- **Shifted numbers that are still plausible** (13 of 95). *"5 swaps past 1, 4 and 2"* shifted to *"6 swaps past
  2, 5 and 3"* names values that are all on screen, and no fact word ties the numbers to a fact. Declared claims are
  the cure: a plan that declares `{"fact": "swaps", "value": 4}` cannot say 6. The planner prompt now asks for them.
- **A changed search argument** (2 of 29). Searching a hash table for 13 instead of 12 leaves the table unchanged;
  the narration still talks about 12, which is a value in the table. The *found* fact differs, but the narration
  says "found" in words the patterns do not read as a claim. Declaring `found` closes it.
- **Dropping a pass whose successor makes no change** (2 of 83). After bubble sort's second pass is dropped, the
  third pass happens to produce the same array the plan claimed, so every state still matches.
- **A changed start node with the same shape** (1 of 20).

## Evaluation harness

`backend/scripts/eval_harness.py` plans and quizzes chosen algorithms with chosen providers and JSON modes, and
records whether a verified lesson came out, the attempts the verifier needed, and the time of every language-model
call (with a call budget for free tiers). `--dry-run` replays the saved plans so the harness itself is tested
offline. The results of a real run are in [eval-json-modes.md](eval-json-modes.md).

In that run (Gemini free tier, plain JSON mode) both lessons came out verified, one after a repair: the model
declared that the settled nodes were "A, C, B, D" but its narration did not say them, and the new claim check sent
the plan back. Schema-constrained output did worse on both speed and correctness, so the Gemini preset no longer
uses it.
