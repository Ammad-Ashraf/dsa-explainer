# Does schema-constrained output slow the planner down?

*Evaluation run of 20 November 2026 with `backend/scripts/eval_harness.py`, Google Gemini free tier.*

**The question.** In a real run before Milestone 7, Gemini took 123 s to plan one lesson and the quiz request timed
out at 180 s twice. Requests were sent with schema-constrained output (`response_format: json_schema` with the
Pydantic schema of a lesson). Was the schema the cause? We measured instead of guessing.

**The run.** Two algorithms (a stack, Dijkstra on a weighted graph), each planned and quizzed once with
`json_schema` and once with `json_object` (plain JSON mode; the prompt still describes the format and Pydantic and
the verifier still check every reply). 14 calls at most, the free tier's daily allowance being about 20 per model.

```bash
python backend/scripts/eval_harness.py --algorithms stack,dijkstra --modes json_schema,json_object --max-calls 14
python backend/scripts/eval_harness.py --summarise outputs/eval/20261120-230908.jsonl
```

| Provider | Model | JSON mode | Runs | Verified lessons | First-try plans | Plan time (median) | Plan call (median) | Quiz time (median) | Quiz from the model | Failed calls | Timeouts |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| env | `gemini-3.5-flash` | json_schema | 2 | 0 | 0 | - | 30 s | - | 0 | 1 | 0 |
| env | `gemini-3.5-flash` | json_object | 2 | 2 | 1 | 37 s | 10 s | 98 s | 4 | 0 | 0 |

Every call, in order:

| Mode | Algorithm | Calls (seconds) | Outcome |
| --- | --- | --- | --- |
| json_schema | stack | plan 258 (failed: connection dropped while waiting) | no lesson |
| json_schema | Dijkstra | plan 163, 17, 32, 29 | no lesson: all four plans wrote the weighted edges in a malformed shape (`edge 4 must look like ["A", "B", 4]`) |
| json_object | stack | plan 57; quiz 58, 123 | verified lesson, 2 questions from the model (the first quiz reply was sent back once) |
| json_object | Dijkstra | plan 6, 10; quiz 8, 8 | verified lesson after one repair (a declared claim the narration did not say); the main model's daily allowance ran out mid-run, so the last three calls used `gemini-3.5-flash-lite` |

**What it shows.** With so few runs this is evidence, not proof, but it points one way:

- Schema-constrained output was **slower** (the first plan call of each run took 163 s and 258 s) and **less
  reliable**: the schema's free-form `initial` field (`Any`, because every algorithm has its own data format) gave
  the model no guidance, and it produced edge lists the simulator rejects, four times in a row.
- Plain JSON mode produced verified lessons for both, with plan calls of 6 to 57 s.
- The quiz is the slow, variable part (58 to 123 s for one call on the main model). That is why Milestone 8 writes
  the quiz while the scenes are voiced and drawn rather than before.

**Decision.** The Gemini preset now uses `json_object` (`authoring/providers.py`). Providers that handle schemas
well keep `json_schema`; the client still steps down by itself when a provider rejects a mode. Re-run the harness
with your own provider before changing a preset: `--providers groq --modes json_schema,json_object`.
