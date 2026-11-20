# Live evaluation

Provider: `https://generativelanguage.googleapis.com/v1beta/openai/`. Main model `gemini-3.5-flash`, fallback `gemini-3.5-flash-lite` (used once the main model's daily free allowance runs out). Updated 05 November 2026 with `python scripts/live_eval.py --render`.

| # | Topic | Level | Expected | Result | Model | Plan attempts | Steps | Words | Quiz | Checks | Plan time | Video |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | How does a stack work? | beginner | lesson | lesson (stack) | `gemini-3.5-flash` | 1 | 5 | 274 | 2 verified | 19 | – | 152 s |
| 2 | Show how a queue handles print jobs | intermediate | lesson | lesson (queue) | `gemini-3.5-flash` | 1 | 6 | 291 | 2 verified | 24 | – | 159 s |
| 3 | How do you insert into the middle of a linked list? | beginner | lesson | lesson (linked_list) | `gemini-3.5-flash` | 1 | 4 | 229 | 2 verified | 16 | – | 148 s |
| 4 | Insert 8, 3, 10, 1, 6, 14 into a BST, then delete 3 | intermediate | lesson | lesson (bst) | `gemini-3.5-flash` | 1 | 6 | 321 | 2 verified | 22 | – | 193 s |
| 5 | Show BFS on this graph: A-B, A-C, B-D, C-E, D-E, start at A | beginner | lesson | lesson (graph) | `gemini-3.5-flash` | 1 | 5 | 243 | 2 verified | 19 | – | 130 s |
| 6 | Explain deleting a node with two children from a binary search tree | advanced | lesson | lesson (bst) | `gemini-3.5-flash-lite` | 1 | 4 | 171 | 1 verified (fallback), 2 attempts | 17 | 6 s | 85 s (made in 40 s) |
| 7 | How does breadth-first search work? | intermediate | lesson | lesson (graph) | `gemini-3.5-flash-lite` | 1 | 5 | 227 | 2 verified, 2 attempts | 19 | 6 s | 124 s (made in 53 s) |
| 8 | Explain heap sort | beginner | refusal | refused | `gemini-3.5-flash-lite` |  |  |  |  |  | 3 s |  |
| 9 | What is the capital of France? | beginner | refusal | refused | `gemini-3.5-flash-lite` |  |  |  |  |  | 10 s |  |

**9 of 9** topics got the expected result. **7 of 7** lessons passed the verifier on the first attempt; every lesson that was accepted passed every check.

## Plans the verifier sent back

None: every plan was correct on its first attempt.

## Refusals

- *Explain heap sort*: Only stack, queue, linked_list, bst, and graph are supported structures.
- *What is the capital of France?*: Only data structures such as stack, queue, linked list, binary search tree, and graph are supported.

## Revisions (on lesson 1, *How does a stack work?*)

| Request | Scenes changed | LLM attempts | Verified | Time |
| --- | --- | --- | --- | --- |
| explain step 2 for a beginner | step 2 | 1 | yes | 4 s |
| make the summary shorter | summary | 1 | yes | 2 s |
