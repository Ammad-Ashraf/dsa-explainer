# DSA Explainer

**Natural Language Processing: Course Project, Fall 2026**
**Project 1: Data Structure Explainer**

| | |
| --- | --- |
| Group | Ahmed Javaid (22i-2530), Ammad Ashraf (22i-2470) |
| Repository | https://github.com/Ammad-Ashraf/dsa-explainer |
| Version | 0.3.0 (MIT licence) |
| Demo video | [DSA Explainer launch video](https://drive.google.com/file/d/1KCi2dclZBBQBWeeuSz0wrhLI8nOqIlPO/view?usp=sharing) (1 min 56 s) |
| Date | November 2026 |

---

## 1. Introduction

Data structures are hard to learn from static diagrams because they change step by step. DSA Explainer turns a
typed question such as *"how does a queue work?"* or *"show Dijkstra from A on this graph"* into a narrated, animated
video lesson that ends with a short quiz. The learner can then ask for a change in plain English, such as *"slow down
step 4"* or *"explain step 2 for a beginner"*, and only that part of the video is made again.

The design follows one sentence from the project brief: **a wrong video is worse than no video.** A language model
is good at planning a lesson and explaining it, but unreliable at tracking state: it may say the top of a stack is 9
when it is 7. So in DSA Explainer the language model never draws and never has the final word on facts. It writes a
*structured plan*; our code runs every step of that plan on real data structures; any mismatch is sent back to the
model together with the true state; and the renderer draws only states that our code computed.

The system covers **22 data structures and algorithms**: stacks, queues, deques, linked lists, binary search trees,
tree traversals, min-heaps, breadth-first and depth-first search, Dijkstra, topological sort, six sorting algorithms,
linear and binary search, hash tables, Fibonacci and coin change. The brief requires linked lists, stacks, queues,
trees and one graph or sorting algorithm.

**What this report describes.** The course submission started with five structures and a Gradio interface. After
that, the project grew into an open-source platform in ten milestones (a local API server, a bring-your-own-model
layer, a React web app, 17 more algorithms, richer animations, pluggable voices, stronger verification with an
evaluation harness, faster builds, packaging, and a topic gate that turns away off-topic requests). This report describes the finished project, version 0.3.0. The
five-structure version is kept where its measurements are reported (Section 8.3).

## 2. Complex Computing Problem analysis

### 2.1 Problem statement

Data structures and algorithms are a core part of every computer science degree, and learners find them hard because
the structures *change*: a pointer moves, a node is replaced, a queue grows and shrinks. Understanding comes from
watching those changes one step at a time, on the learner's own question, at the learner's own level, and with
someone explaining why each step happens.

The existing options each cover only part of this:

- **Textbooks and slides** show still pictures of a few states. The learner has to imagine the transitions.
- **Algorithm visualisation websites** animate correct states, but only for fixed algorithms and the examples they
  were built with. They do not explain in words adapted to a beginner or an advanced student, they cannot answer a
  question phrased in the learner's own words, and they do not quiz the learner.
- **Recorded lectures** explain well, but the example, the pace and the level are fixed. A learner cannot ask for
  "step 4 again, slower" or "the same idea with my numbers".
- **General-purpose AI chatbots** answer any question in any style, but they track state unreliably. They can say,
  confidently, that the top of a stack is 9 when it is 7, or list a BFS order that skips a node. They also produce
  text, not a synchronised animation, and **AI video generators** draw freely, so nothing guarantees that the picture
  shows the true state.

The gap is a tool that is **flexible** like a chatbot (any phrasing, the learner's own data, three levels, changes on
request) and at the same time **guaranteed correct** like a hand-built visualiser, delivered as a narrated video with a
quiz on an ordinary laptop. A standard solution does not close this gap, because the two halves pull in opposite
directions: the component that gives flexibility (a language model) is exactly the one that cannot be trusted with
facts, and the components that are exact (simulators, fixed animations) cannot understand free-form requests.
Combining them so that each covers the other's weakness is the problem this project solves.

### 2.2 Complexity drivers

- **Conflicting requirements.** The brief asks for open-ended input ("a learner types a topic") *and* for correctness
  ("a wrong video is worse than no video"). Free text cannot be checked directly, so we had to design an
  intermediate representation, the JSON scene plan, that is expressive enough for a language model to write and
  precise enough for code to check step by step (Section 5.2).
- **No complete solution for checking language.** Operations and states can be checked exactly, but narration is free
  English. There is no known method that verifies every sentence. We check what can be checked: the facts a plan
  declares, the statements the patterns recognise (top, front, root, size, distances, counts, and many paraphrases of
  them) and every number mentioned (Section 5.3). We measured what still gets through (3% of 601 planted mistakes,
  Section 8.4) and documented it (Section 9).
- **Many components that depend on each other.** The plan format must match 22 simulators, the drawers that show
  them, the pseudocode lines each operation runs, the quiz's fact names and the revision rules. Audio length decides
  animation timing. The cache key of a clip must include everything the clip shows, or a revision would show a stale
  picture. A change in one component breaks others unless the contracts are kept, so every algorithm is one class in
  a registry that the planner prompt, the verifier, the quiz, the renderer, the API and the web app all read from,
  and 303 backend tests, including property-based, golden-layout and mutation tests, guard the contracts.
- **Non-deterministic and imperfect input from many providers.** The language model may return invalid JSON, a wrong
  state, an impossible operation, a refusal, or nothing at all because of an outage or a rate limit, and different
  providers behave differently. In our own measurements, schema-constrained output made Gemini *slower and less
  reliable* than plain JSON mode (Section 8.5). Every failure has to end in either a verified lesson or a clear
  message, never in a wrong video.
- **Hard resource limits.** Text to speech must run locally (brief), on a CPU, and every video must last at least
  30 seconds, which means minutes of speech and thousands of frames per lesson. The quiz call alone can take one to
  two minutes on a free tier. Writing the quiz while the scenes are voiced and drawn cut a 128-second lesson from
  182 to 211 s down to 136 to 155 s, and the first scene can be watched about twice as soon (Section 8.6).
- **Open licences against a good voice.** The best open voice we found (Kokoro) phonemises through a GPL-licensed
  library, while we want an MIT project. This needed research of eleven voice models and a documented position
  (Sections 2.5 and 5.5).
- **External limits found only in testing.** Gemini's free tier allows 20 requests a day per model. Our live
  evaluations ran into it, which forced an automatic fallback model and per-minute retry logic (Section 5.2).

### 2.3 Design justification

For each major decision we considered at least two approaches. The table lists the alternatives we rejected and why.

| Decision | Chosen | Alternative considered | Why we rejected it |
| --- | --- | --- | --- |
| How the animation is produced | The model writes a plan of operations; our renderer draws states computed by our simulators | **The model writes the animation code itself** (for example Manim code), or an AI video generator draws the video | Generated code can run without errors and still show wrong states, so correctness could not be checked. Running model-written code is also a security risk, and a failure is hard to repair automatically. The brief also says the model should not draw freely. |
| How a plan is checked | Running every step on real data structures in Python | **A second language model as a judge** of the first one's plan | A judge model can be wrong in the same way as the planner, gives different answers on different runs, doubles the number of API calls (a problem with a 20-requests-a-day free tier), and cannot produce the true state to send back. A simulation is exact, takes milliseconds and explains every rejection. |
| Where the lesson content comes from | A language model, constrained by a schema and checked by the verifier | **Fixed templates without a language model**, one hand-written lesson per structure with the values filled in | Templates cannot answer a question in the learner's own words, adapt to three levels, use the learner's own data or rewrite a scene on request, which is the natural-language part of the project. We kept the idea only as a safety net: the fallback quiz questions are built from the lesson by code, and the 22 saved lessons play without any model. |
| Which language model | Any provider the learner chooses (Gemini by default) through one OpenAI-compatible client, with a settings page for keys | **A small local model only (Ollama)**, as in our Assignment 3, or **one hard-wired provider** | On this laptop's CPU, the 3-billion-parameter model from Assignment 3 took 6.6 to 16 seconds just to start answering, and models of that size are much weaker at long structured output. Hard-wiring one provider ties every user to one company's free tier and limits. Ollama and LM Studio still work as presets. |
| How a narration claim is checked | Declared claims (each fact the narration states, checked at its exact moment) plus pattern rules and a check on every number | **A natural-language inference model** that judges whether each sentence follows from the true state | It would need an extra model on the CPU, would be slower, and would itself make mistakes we could not explain. The rules cover the facts that matter most, and the mutation tests measure how many wrong sentences they catch (97%). |
| How the quiz's wrong options are made | Simulated mistakes: forgetting the last operation, doing two in the wrong order, treating a queue as a stack; each one is run on the real structure | **The model writes the wrong options**, or **random values** | Model-written options are often not wrong, or wrong in ways nobody makes, and need checking anyway. Random values are obviously wrong and teach nothing. A simulated mistake is exact, differs from the right answer by construction and lets the app say *which* mistake the learner made. |
| How the video is built | One clip per scene, cached by content and joined with ffmpeg | **One continuous video per lesson** | Any change, even "slow down step 4", would force the whole video to be drawn again, so revision control could not change "only that part". Separate clips can also be drawn in parallel, and the first one can be watched while the others are still being made. |
| How the model's reply is constrained | Plain JSON mode, plus Pydantic and the verifier on every reply | **Schema-constrained output** (`json_schema`) | Measured on Gemini: the first plan call took 163 s and 258 s, and four plans in a row had malformed edge lists, because every algorithm has its own data format that one schema cannot describe. Plain JSON mode produced verified lessons for both test algorithms (Section 8.5). |
| How new algorithms are added | A registry: one class per algorithm that carries its simulator, metadata, pseudocode and facts | **Special cases spread through the planner, verifier and renderer**, as in the first version | Adding one algorithm touched six places and the prompt, so the lists drifted apart. With the registry, each of the 17 new algorithms is a new class (and sometimes a new picture) with no special case in the planner, verifier, quiz or API. |
| The user interface | A React web app on a local API server with live job events | **Keeping the Gradio app** | Gradio could not show the pipeline live, play scenes as they were drawn, pick a voice or show pseudocode beside a library page. The API also lets other tools use the same engine. |
| Which voice | Kokoro-82M (ONNX, local), behind an engine interface | **Piper**, which we used in Assignment 3, or **Kitten TTS** | Both are much faster (real-time factor 0.03 and 0.11 against 0.48 for Kokoro, measured), but Piper sounded robotic in Assignment 3, published comparisons rate both below Kokoro, Piper's code became GPL-3.0, and Kitten speaks slowly. A lesson video does not need real-time speech, so we chose the more natural voice and overlapped it with drawing. The engine interface keeps the others one class away. |

### 2.4 Trade-off analysis

| Trade-off | Our choice | Reason |
| --- | --- | --- |
| **Correctness vs. coverage** | 22 algorithms, each with an exact simulator, and a polite refusal for anything else | Every supported topic can be verified. Explaining an algorithm without a simulator would mean showing an unchecked video, which the brief calls worse than none. In the live evaluation, both off-topic requests were refused (Section 8.3). Coverage grew from 5 to 22 by adding simulators, never by relaxing checks. |
| **Fast refusal vs. one more model call** | A topic gate before planning: a keyword match, else a short classifier call to a lighter model; if the check fails, the planner decides | Refusing inside the planner cost a full planning call: 142 s for "What is the capital of Pakistan". The gate refuses it in 1.5 s. Topics that name an algorithm pass on a keyword with no extra call, and only topics with no keyword pay for the classifier (about a second). The gate never blocks on its own failure, so the worst case is the old behaviour plus at most the gate's timeout (Section 8.9). |
| **Strict checking vs. complete checking of language** | Declared claims and rule-based checks that catch wrong values and false facts (97.0% of 601 planted mistakes), but not wrong reasons or poor analogies | Deterministic, fast and explainable checks rather than a slower second model that could also be wrong. We chose to measure and publish the 3% that gets through (Section 8.4) rather than claim the whole lesson is correct. |
| **Reliability vs. waiting time** | Up to four planning attempts and a quiz repair before giving up | Each repair adds a few seconds, but a wrong video is never shown. In our Gemini runs one of two lessons needed a repair, and the claim check caught a narration that did not say what the plan declared. |
| **Latency vs. a simple pipeline** | The quiz is written in a background thread while scenes are voiced and drawn, and its clips are added last | The quiz is the slowest model call (8 to 123 s). Overlapping it saves 46 to 56 s, at the price of a more complex job runner and a fallback when the quiz arrives late or fails. |
| **Picture readability vs. problem size** | At most 7 to 8 items or nodes | Larger structures do not fit on screen with readable labels. Small examples are also what teaching usually uses. |
| **Voice quality vs. speed** | Kokoro, about twice as fast as real time on four cores, overlapped with drawing | The natural voice costs about 50 seconds per two-minute lesson. Overlapping it with drawing hides most of the drawing time. Voice threads and GPU providers are settings for slower machines. |
| **Captions: always on vs. off by default** | Captions exist for every video but start off | Every scene already shows its own caption on screen, and the two overlapped. Learners who need them turn them on, and a full transcript is in the lesson page. |
| **Video quality vs. speed** | 480p "draft" by default; 720p "standard" and 1080p "high" on request | Draft is faster and good enough while trying topics; the higher qualities are there for the final video. |
| **Cost vs. model quality** | The free Gemini tier, switching to the smaller Flash-Lite model after the daily allowance, or any other provider | The project costs nothing to run. The smaller model's quiz questions failed verification more often, but the verifier caught every one. A paid key removes the limit. |
| **Fixed conventions vs. teaching variety** | BFS takes neighbours in alphabetical order; a BST delete uses the in-order successor | A fixed rule makes every state checkable and every quiz answer unique. Courses that teach the predecessor would need a setting. |
| **Disk space vs. revision speed** | Keep every narration and clip in a cache | A revision then redraws only the changed scene, about 10 seconds instead of a full minute, at the cost of a few megabytes per lesson. |
| **Open licence vs. best voice** | MIT for our code; Kokoro stays the default although its phonemiser is GPL-3.0 | The GPL part is a separately installed dependency, not shipped code, and both notices say so. Anyone who bundles an installer must follow the GPL; the voice research describes a path to a GPL-free phonemiser. |

### 2.5 Societal and ethical impact

**Benefit and accessibility.** The tool gives any learner a patient, personalised explanation: their own question and
data, their level, the pace they ask for, and a quiz to check understanding. It runs on an ordinary laptop with no GPU,
and the voice and animation are made locally, so it does not need a paid service apart from the language model, which
has a free tier or can be a model running on the learner's own computer. It is open source (MIT), so teachers can read
it, change it and add their own algorithms, and the 22 saved lessons work with no key at all.

**Accuracy and over-trust.** Learners tend to trust a confident, polished video, so a wrong AI explanation can do real
harm to learning. This is the main ethical risk of the idea, and the main reason for the design: every state, every
checked fact and every quiz answer is verified, and a lesson that cannot be verified is not shown. The remaining risk
is narration that the rules cannot check, such as a wrong reason; in our mutation tests 3% of planted mistakes still
passed. The "Verified" tab lists exactly what was checked rather than claiming that the whole lesson is correct, and
the limitation is stated in this report and the README.

**Privacy.** The typed topic and the lesson text are sent to the language-model provider the learner chooses (for
example Google for Gemini); nothing else leaves the computer, and with Ollama or LM Studio nothing leaves at all.
Learners should not type personal information into the topic box, and on free tiers a provider may use requests to
improve its services, so the provider's terms apply. The voice, the animation and the videos stay on the user's
computer. The app has no accounts, no tracking and no analytics. API keys are stored in `settings.json` in the data
folder, which is excluded from the repository, and are redacted from logs and error messages (a test checks that no
key leaks).

**Safety and security.** The model never runs code: it can only choose operations from a fixed list (such as `push` or
`insert`), and those are carried out by our own simulators. A topic that tries to change the instructions (a prompt
injection) can at worst produce a plan that fails validation or verification. Off-topic requests are turned away by
a topic gate before any lesson is planned (Section 5.2). The
server listens on the local address only.

**Legal and licensing.** Our code is MIT. The components are open source: Manim (MIT), the Kokoro-82M weights (Apache
2.0), `kokoro-onnx` (MIT), FastAPI (MIT), React (MIT) and the bundled Nunito font (SIL Open Font Licence);
`THIRD_PARTY_NOTICES.md` lists every dependency with its licence. The voice's pronunciation step uses espeak-ng
through `phonemizer`, which is GPL-3.0 and installed as a dependency. That is fine for the source and for coursework,
but anyone who ships a bundled installer would have to follow the GPL, and both notices say so. Use of a model API is
governed by the provider's terms. Our own use of an AI coding assistant is disclosed in Section 10.

**Fairness.** The app works only in English, and its voices are American and British English, which may suit some
learners less than others. A learner with only a free API key gets the smaller fallback model once the daily
allowance runs out, so the quality of the explanation can depend on what the learner can pay for; local models are
the free alternative. Learners with hearing impairments get captions on every video (a WebVTT track) and a full
transcript in the lesson page, and the animation and pseudocode show each step without sound.

## 3. Requirements and how they are met

| Requirement from the brief | How DSA Explainer meets it |
| --- | --- |
| A learner types a topic; the system plans a lesson, writes the narration, draws the animation, adds a voice and exports a video with a quiz at the end | Web app → API server → topic gate → lesson planner → step verifier → voice, quiz and renderer → one mp4 with captions |
| Cover at least linked lists, stacks, queues, trees and one graph or sorting algorithm | 22 algorithms in seven families, each with its own simulator and picture: stack, queue, deque, linked list, BST, tree traversals, min-heap, BFS, DFS, Dijkstra, topological sort, six sorts, two searches, hash table, Fibonacci and coin change |
| Every video is at least 30 seconds long | The verifier rejects plans with too little narration (about 36 s of speech). Real lessons last about 1.5 to 2.5 minutes |
| The language model produces a structured scene plan that the renderer draws | A JSON scene plan, validated with Pydantic. The renderer reads only the verifier's snapshots |
| The system checks that the explanation is correct | Every operation is run on a real data structure; claimed states, declared claims, narration facts, numbers and quiz answers are checked; 97.0% of 601 planted mistakes are caught |
| Text to speech runs locally | Kokoro-82M through ONNX on the CPU, behind a pluggable engine interface |
| A user interface usable without touching the code | A React web app: Studio, Library, My lessons and Settings |
| Runs on a normal laptop by following the README | CPU only; one command (`dsa-explainer`) after installing; CI builds and tests it on Windows, macOS and Linux (Section 8.2) |

The core modules are described in Section 5.

## 4. System architecture

![DSA Explainer system architecture](architecture.png)

1. The learner types a topic and picks a level (beginner, intermediate or advanced) in the **web app**, which talks to
   the **local API server**. The server runs one job at a time and streams its progress live.
2. The **topic gate** checks that the request is about one of the 22 algorithms: by keyword, or else with one
   short call to a lighter model. An off-topic request stops here, in about a second, with a message that lists
   what is supported.
3. The **lesson planner** sends the topic, the level and the reference of the algorithms the topic names (or the one
   the gate recognised) to the language model the learner chose, which returns a JSON scene plan.
4. The plan is checked against a Pydantic schema, and then the **step verifier** runs it on the real simulator.
   Any problem is sent back to the planner together with the true state, for up to four attempts in total. If no
   attempt passes, no video is made.
5. **Kokoro** (or another voice engine) speaks each scene's narration on the local CPU, one sentence at a time, so
   caption times are exact. As soon as a scene's audio exists, the scene is handed to one of several drawing
   processes, and the **renderer** (Manim) draws it from the verifier's snapshots, timed to the audio. Each scene is
   announced to the web app as soon as it is drawn, so the first scene can be watched while the rest are made.
6. At the same time, the **quiz writer** (a background thread) asks the model for questions. The verifier recomputes
   every answer, and wrong options come from simulated mistakes. The quiz clips are added last.
7. Each clip is stored in a cache under a hash of everything it shows and says, and **ffmpeg** joins the clips into
   `lesson_v1.mp4`; the sentence times become one WebVTT captions file.
8. A change request goes through **revision control**, is verified again, and only the clips whose content changed
   are drawn again.

## 5. Core modules

Code paths are inside `backend/dsa_explainer/`.

### 5.1 Algorithm registry and simulators (`algorithms/`)

Every algorithm is one plain Python class in a registry, grouped by family (`linear`, `trees`, `graphs`, `arrays`,
`hashing`, `dp`). A class lists its operations, runs them (`run`), and reports its plain state (`state`), named facts
such as top, front, root, size, in-order traversal, BFS order, distances, comparisons or swaps (`facts`), and a
snapshot with a stable id per element for the animation (`snapshot`). It also carries its own metadata: title,
category, difficulty, complexity, description, pseudocode, keywords, example data, the fact words the verifier
recognises, which picture draws it, which facts to show in the strip above the picture, and which pseudocode lines
each operation runs (refined from what the simulator actually did, for example binary search's left or right branch).
Impossible operations raise an error, for example *"cannot pop: the stack is empty"*. Conventions are fixed and given
to the model: a BST has no duplicates and a node with two children is replaced by its in-order successor; BFS and DFS
take neighbours in alphabetical (or numeric) order.

Because everything else reads from the registry, adding an algorithm means writing one class and, if needed, one
picture; the planner, verifier, quiz, renderer, API and Library page need no change. Every simulator is tested against
an independent reference implementation with property-based tests (Hypothesis), which found two real bugs (selection
sort on one value, and a graph edge given twice), both fixed.

### 5.2 Topic gate, lesson planner and providers (`authoring/gate.py`, `authoring/planner.py`, `core/lesson.py`, `authoring/llm.py`, `authoring/providers.py`)

**Topic gate.** Before the planner is called, `gate.py` decides whether the request is something the app can
explain. The first version had no such step: the planner prompt's last rule asked the model to reply
`{"error": "unsupported"}` for other topics, so an off-topic request paid for the most expensive call there is. With
no algorithm named, the prompt carried the reference of all 22 algorithms and the reply was constrained by the whole
lesson schema; "What is the capital of Pakistan" took 142 s to be refused. The gate answers in two tiers:

1. **Keywords.** Every algorithm class lists its keywords (`KEYWORDS`), which the planner already used to choose
   which reference to send. A topic that matches one ("bubble sort", "FIFO", "undo") is in scope at once, with no
   API call.
2. **A short classifier call**, only when no keyword matched. The prompt lists the 22 names and titles and asks for
   `{"in_scope", "structure", "reason"}`, with examples of paraphrases that are in scope ("the shortest route between
   cities" is Dijkstra). The call goes to the provider's fallback model (`gemini-3.5-flash-lite` for Gemini; settable
   with `GATE_MODEL`), at low reasoning effort, without rate-limit waits and with a 10 s timeout. Providers that do
   not know the reasoning-effort option are asked again without it.

An off-topic request ends the Plan stage at once with a fixed message naming the seven families that are supported.
An in-scope paraphrase passes the recognised algorithm to the planner, which then sends only that algorithm's
reference, a shorter prompt. The gate **fails open**: if the classifier errors, times out or replies with something
unreadable, the request goes on to the planner as before, and the planner's own refusal rule stays as a second line.
An outage of the light model therefore never blocks a valid topic. The gate's verdict, its tier and its time are
sent to the web app as an event and saved with the lesson's timings; `TOPIC_GATE=0` turns it off for comparisons.

The planner turns a topic and a learner level into a `Lesson`: a title, the algorithm, its initial data and a list of
scenes. A plan has one intro scene, several step scenes and one summary scene. Each step holds exactly one operation,
the state the model expects after it (`claimed_state`), the facts its narration states (`claims`), a short on-screen
caption and the narration. One step from the saved stack lesson:

```json
{
  "kind": "step",
  "caption": "push(7)",
  "op": {"name": "push", "args": {"value": 7}},
  "claimed_state": [4, 9, 2, 7],
  "claims": [{"fact": "top", "value": 7, "when": "after"}],
  "narration": "Next we push 7. Again it goes on the top, above 2. The stack keeps items in the order they arrived, with the newest one on top. The top is now 7."
}
```

**Prompt design.** The reference of the algorithms, their operations and their state formats is generated from the
simulator classes themselves, and only the algorithms a topic names are sent, so the prompt and the verifier can never
disagree. The rules ask for plain spoken sentences, digits for numbers, short scenes, small values, at most 7 to 8
items, a style that matches the level (analogies for beginners, time complexity for intermediate, edge cases and
trade-offs for advanced), the learner's own data when they give it, declared claims for the facts the narration
states, and a JSON `{"error": "unsupported"}` reply for topics outside the registry.

**Validation and repair.** The reply is parsed (code fences and surrounding text are tolerated) and validated with
Pydantic. The step verifier then runs it. If anything is wrong, the errors are sent back as a new message, for
example *"step 2 (push(7)): claimed_state [4, 9, 7] is wrong; the real state after this step is [4, 9, 2, 7]"*, and
the model returns a corrected plan. After four failed attempts the planner stops and no video is made.

**Any provider.** `llm.py` talks to any OpenAI-compatible chat API through a `Client` per provider configuration, so
Gemini (the default), OpenAI, Anthropic (through its compatible endpoint), Groq, OpenRouter, Ollama, LM Studio or any
custom URL can be used, chosen in the Settings page or in `.env`. Each preset records its base URL, models, key page
and preferred JSON mode (Gemini uses plain JSON mode, Section 8.5). Free tiers are tight: Gemini's allows a few
requests per minute and only 20 per day for each model. When the provider answers "rate limited", the client waits and
tries again. When the limit is the *daily* one, waiting does not help, so the client switches to a fallback model with
its own allowance (`gemini-3.5-flash-lite`), and the report names the model that was used. A client steps down by
itself when a provider rejects a JSON mode. Keys are redacted in logs and errors.

### 5.3 Step verifier (`core/verifier.py`, `core/mutants.py`)

The verifier checks a plan at six levels:

1. **Shape:** one intro first, one summary last, enough steps, and enough narration so the video lasts more than
   30 seconds.
2. **Operations:** every step's operation must be possible on the current state.
3. **States:** every `claimed_state` must equal the true state after the step. Values are compared as text, so `5`
   and `"5"` match, and trees are compared as nested structures.
4. **Declared claims:** each `{fact, value, when}` must be exactly true at its moment (before or after the step), and
   the narration must say the value.
5. **Narration statements:** regular expressions find statements such as "the top of the stack is now 7", "5 sits at
   the front", "the stack holds three values", "D drops to 8" or "after three comparisons". Each is compared with the
   true facts right after the step (or before it, when a claim declares so). Sentences that are not claims ("this is the
   root of the problem") are ignored.
6. **Stray numbers:** every number in the narration must be a value of the structure, an argument of the operation, or
   one of the simulator's own counts at that moment (comparisons, swaps, size, indices, distances). This catches
   invented values, such as "we push 12" in a step that pushes 7.

Quiz questions are checked the same way (Section 5.6). The verifier also produces one *frame* per scene (the
snapshots before and after it, the elements to highlight, the pseudocode lines run and the facts before and after),
and these frames are the renderer's only input.

**Two gaps found and closed.** While writing the saved plans we found that a fact true either before or after a step
was accepted (*"the root is 1"* on the step that removes 1), and that any number from 0 to 8 passed as a "count"
(*"D drops to 7"* when Dijkstra gives 8). Both are now rejected and are regression tests.

**Measuring the verifier.** `core/mutants.py` plants one mistake at a time in each saved lesson, in ten ways, and the
verifier must reject every mutant (Section 8.4). The checks are rule-based on purpose: they are deterministic, run in
milliseconds, need no second model that would itself have to be trusted, and every rejection can be explained. The
limitation is that they cannot judge every sentence (Section 9).

### 5.4 Animation renderer (`media/render.py`, `media/views/`, `media/panels.py`)

The renderer uses Manim Community 0.22 with its Cairo backend (no LaTeX needed) and makes one short clip per scene.

**Drawers.** Each algorithm names a *view*, and a view turns a snapshot into a dictionary of named shapes. Views are
grouped by picture, since many algorithms share one: stack, queue and list (`linear`), tree and heap (`tree`), graph,
array (bars and cells with pointers and ranges), and hash buckets and DP tables (`table`). Keys are element ids, so the
same shape can be followed from one picture to the next.

**One animation for every operation.** To animate a step, a single `morph` function moves every shape whose key
exists in both pictures, fades out the keys that disappeared and fades in the new ones. In the array and heap views, a
value that moves travels on an arc, so two values that swap visibly pass each other.

**Choreography of a step:**

1. walk the path the operation takes (the nodes compared in a BST, the cells scanned in a search, the node leaving a
   queue);
2. morph into the true state after the operation, with the path in blue and new elements in green;
3. pulse what is new;
4. hold until the narration ends;
5. return to plain colours, so the next clip starts from exactly the same picture.

**What the video teaches beyond the picture.** Beside the structure is a *pseudocode card* with the lines the step ran
highlighted, and above it a *facts strip* (for example comparisons, swaps, the pivot or distances) that updates with
every step and marks what changed. Both come from the simulator, not from the language model.

**Look and layout.** Videos use a light theme taken from the app's design system (white stage, green for new and done,
blue for the path, orange for the current element) with the Nunito font bundled and registered, so every machine draws
the same letters. They are made at 854×480 and 15 fps ("draft"), 1280×720 and 30 fps ("standard") or 1080p ("high").
Layout regression tests compare the centre and size of every shape in every saved lesson with approved JSON, instead
of comparing screenshots, which differ between systems.

### 5.5 Narration and voice (`media/voices/`, `media/video.py`)

Voices sit behind an `Engine` interface (`voices()` and `synthesize()`), with **Kokoro-82M** (82 million parameters,
Apache 2.0 licence, through `kokoro-onnx` on the CPU) as the first engine and the default. No speech API is used. The
Settings page lets the learner pick an engine and a voice (28 English voices, grouped by accent), set the speed and
play a short preview. We researched eleven candidate models for their licences, CPU speed, timestamps and Windows
support (`docs/research/voice-models.md`) and measured three of them (Section 8.7).

**Pronunciation.** A lexicon rewrites what is *spoken* (not what is shown): notation such as `O(n log n)`, `a[i]`,
`push(7)`, `->` and `<=`, acronyms such as BFS, and words the voice gets wrong such as "deque" and "Dijkstra". It is
part of the audio cache key.

**Synchronisation and captions.** Each sentence is synthesised on its own and joined with a 0.25 s pause, so sentence
times are exact (no CPU voice engine we found exposes word times). Each scene's clip is timed to its audio: the
animation phases fit inside the narration, and the scene then holds until the narration ends. A short silent pad makes
each clip's audio track cover the whole clip, so the joined video stays in sync (on a 10-clip lesson the video track
lasts 142.58 s and the audio track 142.63 s). Every lesson version also gets a WebVTT captions file; the player shows
it as a captions track that is off until the learner turns it on, because every scene already shows its own caption.

**Caching and speed.** Audio files are named by a hash of the engine, the voice, the speed and the text, so a narration
that did not change is never spoken again. Revisions can change a scene's speed, which slows the speech and stretches
the animation. ONNX threads and execution providers (for example DirectML or CUDA, with the CPU as the fallback) are
settings.

### 5.6 Quiz writer (`authoring/quiz.py`, `authoring/mistakes.py`)

The model receives the lesson's initial data, its operations, its final state and the reference for the algorithm, and
writes the quiz questions. Every question carries its own start data, operations, the name of the fact being asked
(for example `front`, `inorder` or `bfs_order`), the options, the answer and a one-line explanation. Question types are
multiple choice, true or false, and counts (comparisons, swaps, nodes walked). The verifier runs the operations on a
fresh structure and checks that the given answer equals the computed fact, that exactly one option is correct, and
that the explanation mentions no numbers from outside the question.

**Wrong options from simulated mistakes.** A good wrong option is the answer to a slightly wrong reading of the
question, so `mistakes.py` simulates typical mistakes on the real structure: forgetting the last operation, running it
twice, doing the last two in the wrong order, using the value before any operation, treating a queue as a stack, BFS as
DFS or one sort as another. An option is kept only when it differs from the true answer, and it carries the reason,
which the app shows when a learner picks it.

**Repair and fallback.** A question with a right answer but broken options is repaired instead of thrown away; wrong
questions are sent back once; and built-in questions cover every algorithm, so a quiz always exists. The quiz is
written in a background thread while the scenes are voiced and drawn, and its clips are added last (Section 8.6). In the
video, each question and its options are read aloud, a three-second timer bar runs, and the correct option is
highlighted while the answer and explanation are spoken.

### 5.7 Revision control (`authoring/revise.py`, `media/video.py`)

**Speed requests** ("slow down step 4", "speed up the summary") are handled by rules, with no model call: the named
scenes play at 0.75× or 1.25× speed.

**Other requests** ("explain step 2 for a beginner", "make the summary shorter") go to the model, which sees each
scene's caption, operation, true state, speed and narration. It may change only the narration, caption, speed,
summary points and level. Operations and values are fixed, so every picture stays verified. The revised lesson is
verified again, with up to three attempts; if it still fails, the old video is kept.

**Only that part changes.** Each clip is cached under a SHA-1 hash of everything it shows and says: the title,
caption, narration, speed, before and after snapshots, highlighted elements, quality and renderer version. After a
revision, unchanged scenes are found in the cache and only the changed ones are drawn. The new video is saved as
`lesson_v2.mp4`, then `lesson_v3.mp4`, and so on. For example, "slow down step 2" drew 1 clip and reused 9, in 5.5 s
of voice and 5.7 s of drawing.

### 5.8 API server and jobs (`api/`, `pipeline.py`, `store.py`, `events.py`)

A FastAPI app serves the web app and a JSON API: the algorithm catalogue, saved plans, lessons and their versions,
jobs, providers and settings, voices and previews, and the video, clip and caption files (with range requests so
players can seek). A job runner takes one job at a time from a queue, and the pipeline reports structured events
(stage, progress, each finished clip, timings) that the browser follows live over Server-Sent Events. Jobs can be
cancelled. Every lesson version saves the duration of each stage, so the app can show where the time went. The API is
tested with a fake language model and fake providers.

### 5.9 Web app (`frontend/`)

A React and TypeScript app (Vite) with these pages. **Home** explains the product. **Studio** has the composer, a
pipeline rail with live timers, a player that plays each scene as soon as it is drawn, chapters, and tabs for the quiz,
what was verified (with a bar chart of where the time went), a box for change requests, the transcript and the plan.
**Library** lists the 22 algorithms by family with search and a difficulty filter; each algorithm page shows its
pseudocode with the lines of a chosen operation highlighted, and a ready-made lesson that needs no key. **My lessons**
lists saved lessons and their versions. **Settings** has the language-model provider, key and model, the voice,
video quality and storage. The design follows our design system with original illustrations, and the app is
responsive and keyboard-friendly.

## 6. Technical details

### 6.1 Models, APIs and where they run

| Part | Model or tool | Where it runs |
| --- | --- | --- |
| Topic gate (is the request about a supported algorithm?) | Keyword match first; otherwise the chosen provider's lighter fallback model (`gemini-3.5-flash-lite` by default), at low reasoning effort | Local, then API or local |
| Lesson planning, narration text, quiz questions, rewrite requests | The learner's choice: Gemini (default), OpenAI, Anthropic, Groq, OpenRouter, any OpenAI-compatible API, or Ollama or LM Studio on the same computer | API, or local |
| Step verifier, simulated mistakes and quiz answer checking | Plain Python | Local |
| Text to speech | Kokoro-82M (ONNX), behind a pluggable engine interface | Local, CPU |
| Animation | Manim Community 0.22 (Cairo), Nunito font | Local, CPU |
| Joining clips | ffmpeg (bundled by `imageio-ffmpeg`), stream copy | Local |
| API server | FastAPI and Uvicorn, on 127.0.0.1 | Local |
| Web interface | React, TypeScript, Vite | Local (in the browser) |

### 6.2 Speed and parallelism

The voice speaks the scenes in order. Each clip is given to a pool of drawing processes as soon as its audio exists, so
speaking and drawing overlap, and the quiz is written at the same time. The clips are joined without re-encoding.

Measured on an AMD Ryzen 5 4500U laptop (6 cores, no GPU), Windows 11, 3 drawing processes, draft quality, each run
from an empty cache:

| Measurement | Result |
| --- | --- |
| Voice speed (Kokoro, real-time factor: time to speak one second of audio) | 0.48 with 4 threads, 0.51 with the default, 1.04 with one thread |
| New 128 s stack lesson, quiz call of 60 s, quiz first (before) | first scene at 120 s and 127 s; finished at 211 s and 182 s |
| The same lesson, quiz written during voice and drawing (after) | first scene at 76 s and 58 s; finished at 155 s and 136 s |
| Revision "slow down step 2": 1 clip drawn, 9 reused | 5.5 s voice + 5.7 s drawing |

Runs on this laptop vary by about 20 s, and two or four voice threads were within that noise, so the default stays. The
language model dominates a new lesson: on Gemini's free tier a plan call took 6 to 57 s and a quiz call 8 to 123 s.
An off-topic request no longer waits for a plan call: the topic gate refuses it in about a second (Section 8.9).

### 6.3 User interface

See Section 5.9. The web app follows a job live: the pipeline rail shows each stage with a running timer, the first
scene plays as soon as it exists, and the **Verified** tab lists the checks that passed, any plans the verifier sent
back, the clips drawn or reused, and the time of each stage.

### 6.4 Code organisation

| Path | Lines | Purpose |
| --- | --- | --- |
| `backend/dsa_explainer/algorithms/` | 2131 | 22 simulators with their metadata, grouped by family, and the registry |
| `backend/dsa_explainer/core/` | 623 | Scene-plan schema, verifier, mutation testing (no AI, no I/O) |
| `backend/dsa_explainer/authoring/` | 1110 | Topic gate, planner, quiz, simulated mistakes, revisions, providers, language-model client |
| `backend/dsa_explainer/media/` | 1526 | Voice engines, lexicon, captions, Manim views and panels, joining |
| `backend/dsa_explainer/api/` | 603 | FastAPI app and job runner |
| `backend/dsa_explainer/` (root) | about 650 | Pipeline, lesson store, events, settings, configuration, command line, model download |
| `backend/dsa_explainer/plans/` | 22 files | The verified saved lessons |
| `backend/tests/` | 2039 | 303 automated tests |
| `backend/scripts/` | | Live evaluation, evaluation harness, mutation report, benchmarks, plan authoring, diagram, report PDF |
| `frontend/src/` | 3017 | React and TypeScript web app |
| `docs/` | | Roadmap, design, research and the course documents |
| `launch-video/` | | Scripted capture and Remotion edit of the demo video |

## 7. Setup and use

```bash
git clone https://github.com/Ammad-Ashraf/dsa-explainer.git dsa-explainer
cd dsa-explainer
python -m venv .venv
.venv/Scripts/activate                       # macOS and Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -e . --no-deps
cd frontend && npm ci && npm run build && cd ..   # the web app (Node 20 or newer)
dsa-explainer
```

`dsa-explainer` downloads the voice model on first run (about 350 MB), starts the app at http://127.0.0.1:8000 and
opens it. Lessons from the Library play straight away. To make lessons from your own topics, open Settings, choose a
provider and paste a key (Gemini and Groq have free tiers; Ollama needs no key). The README gives the full
instructions, including the command line (`dsa-explainer "how does a stack work" --level beginner`) and how to install
from the wheel that CI builds.

## 8. Testing and evaluation

### 8.1 Automated tests

`python -m pytest backend` runs **303 tests in about two minutes**, and all of them pass (including real clip renders
with the voice model; tests that need the voice model skip without it). `ruff check .` is clean. In the web app,
`npm test` runs 8 unit tests and `npm run build` runs the type check, ESLint and the production build.

| Tests | Count | What they check |
| --- | ---: | --- |
| Algorithms | 85 | Every operation of every simulator, impossible operations, the conventions, and property-based comparisons with reference implementations |
| Verifier | 50 | Each kind of mistake is caught (wrong state, false narration fact, invented number, impossible operation, wrong quiz answer, too-short lesson, declared claims, paraphrases); both closed gaps are regression tests |
| Quiz and revisions | 33 | Answers are computed, wrong questions repaired, options from simulated mistakes, fallback questions for every algorithm; "slow down step 4" changes only step 4; a rewrite that states a false fact is sent back |
| Layouts and views | 45 | The centre and size of every shape in every saved lesson against approved JSON; every view draws every algorithm |
| Voices | 23 | Engine interface, sentence timing, captions, lexicon, cache keys |
| Providers | 13 | Presets, keys never leaked, rate limits and fallback models |
| API | 12 | Lessons, jobs and events, settings, saved plans (with a fake language model) |
| Topic gate | 14 | Keyword topics need no API call; off-topic requests stop in the Plan stage without planning; a recognised algorithm narrows the planner prompt; the gate fails open on errors, bad replies and timeouts; quick calls use the given model at low reasoning effort, retry without that option when a provider rejects it, and never wait on a rate limit |
| Structures, planner, mutation, harness, pipeline, rendering | 28 | Data structure basics, planner repair with a fake model, the mutation-rate floor, the evaluation harness offline, a full pipeline run, real clips with sound |

### 8.2 Installation and continuous integration

The course version was cloned into an empty folder and set up exactly as its README described: a new virtual
environment, the install, the voice download, the test suite and a video from a saved plan. Every step worked. Since
then we added packaging (a root `pyproject.toml`, the `dsa-explainer` command and a wheel that bundles the web app)
and a GitHub Actions workflow that runs the backend tests, `ruff` and the command on Windows, macOS and Linux
(Python 3.12, plus 3.13 on Linux), runs the web app's tests and build, and builds and checks the wheel. **The workflow
has been pushed but had not yet run on GitHub when this report was written, so the macOS and Linux runs are untested.**
The rest of the report was measured on Windows.

### 8.3 Live evaluation with Gemini (course version)

`backend/scripts/live_eval.py` sends nine requests to the real model: seven supported topics across all five
structures of the course version and all three levels (two of them with data typed by the learner), and two topics
that must be refused. It also makes every accepted lesson into a video, and tries two rewrite revisions. The full
results are in `docs/course/live-eval.md`. The run was made before the registry grew to 22 algorithms, so heap sort was
still outside the scope and was correctly refused; it is now supported.

| # | Request | Level | Model | Result | Plan attempts | Quiz | Video |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | How does a stack work? | beginner | 3.5 Flash | lesson | 1 | 2 verified | 152 s |
| 2 | Show how a queue handles print jobs | intermediate | 3.5 Flash | lesson | 1 | 2 verified | 159 s |
| 3 | How do you insert into the middle of a linked list? | beginner | 3.5 Flash | lesson | 1 | 2 verified | 148 s |
| 4 | Insert 8, 3, 10, 1, 6, 14 into a BST, then delete 3 | intermediate | 3.5 Flash | lesson | 1 | 2 verified | 193 s |
| 5 | Show BFS on this graph: A-B, A-C, B-D, C-E, D-E, start at A | beginner | 3.5 Flash | lesson | 1 | 2 verified | 130 s |
| 6 | Explain deleting a node with two children from a BST | advanced | 3.5 Flash-Lite | lesson | 1 | fallback question after 2 rejected attempts | 85 s |
| 7 | How does breadth-first search work? | intermediate | 3.5 Flash-Lite | lesson | 1 | 2 verified on the 2nd attempt | 124 s |
| 8 | Explain heap sort | beginner | 3.5 Flash-Lite | refused (not supported then) | | | |
| 9 | What is the capital of France? | beginner | 3.5 Flash-Lite | refused | | | |

What the run shows:

- **9 of 9 requests got the expected result:** seven lessons and two refusals.
- **All seven lesson plans passed the verifier on the first attempt**, including both learner-typed data sets, the
  binary search tree delete with a successor swap and the advanced level. Every accepted lesson passed every check.
- **The verifier caught wrong quiz answers.** With the smaller fallback model, the questions for lesson 7 were
  rejected once and corrected, and the questions for lesson 6 were wrong twice, so that lesson received the question
  built from the lesson itself. No wrong answer reached a video.
- **Rewrite revisions changed only the part asked for:** "explain step 2 for a beginner" changed step 2, and "make
  the summary shorter" changed the summary. Both passed verification on the first attempt, in 4 s and 2 s.
- **Free-tier limits are real.** After lesson 5 the run reached Gemini's limit of 20 requests a day for
  `gemini-3.5-flash`. This led us to add the automatic fallback model (Section 5.2), which carried out lessons 6 to 9
  and the revisions.

### 8.4 How many mistakes does the verifier catch?

`backend/scripts/mutation_report.py` plants one mistake at a time in each of the 22 saved lessons, in ten ways, and
runs the verifier on every mutant. A mutant is *caught* when the verifier reports an error. Mutants that teach exactly
the same thing as the original are not counted, because accepting them is correct.

| Mistake planted | Mutants | Before Milestone 7 | Now |
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

A test keeps the six "always caught" rows at 100% and the overall rate at or above 96.5%, so the rate can only go up.
What still gets through (about 3%): shifted numbers that are still plausible (13 of 95), a changed search argument
that leaves the structure unchanged (2 of 29), a dropped pass whose successor happens to make no change (2 of 83), and
a changed start node with the same shape (1 of 20). Declared claims close most of these, which is why the planner
prompt asks for them. The details are in `docs/research/verification.md`.

### 8.5 Does schema-constrained output help? (evaluation harness)

`backend/scripts/eval_harness.py` plans and quizzes chosen algorithms with chosen providers and JSON modes, records
whether a verified lesson came out, how many attempts the verifier needed and the time of every model call, with a call
budget for free tiers (`--dry-run` replays the saved lessons so the harness is tested offline). In a real Gemini run,
two algorithms (a stack and Dijkstra) were planned and quizzed once with schema-constrained output (`json_schema`) and
once with plain JSON mode (`json_object`), 14 calls in all:

| JSON mode | Runs | Verified lessons | First-try plans | Plan call (median) | Failed calls |
| --- | ---: | ---: | ---: | ---: | ---: |
| `json_schema` | 2 | 0 | 0 | 30 s | 1 |
| `json_object` | 2 | 2 | 1 | 10 s | 0 |

Schema-constrained output was slower (the first plan calls took 163 s and 258 s, one of them failing) and less reliable
(four plans in a row wrote the weighted edges in a shape the simulator rejects). Plain JSON mode produced two verified
lessons, one after a repair: the model declared that the settled nodes were "A, C, B, D" but its narration did not say
them, and the claim check sent the plan back. With so few runs this is evidence, not proof, but we changed the Gemini
preset to plain JSON mode, and the harness lets anyone re-measure their own provider. The full table is in
`docs/research/eval-json-modes.md`.

### 8.6 Speed

The latency measurements are in Section 6.2. Writing the quiz while the scenes are voiced and drawn saves 46 to 56 s,
most of the quiz call, and the first scene can be watched about twice as soon. `backend/scripts/latency_benchmark.py`
reproduces them.

### 8.7 Voice engines

`backend/scripts/voice_benchmark.py` and `docs/research/bench_other_engines.py` measured the real-time factor (seconds
of computing per second of audio; below 1 is faster than real time) on the same text:

| Engine | Real-time factor | Note |
| --- | ---: | --- |
| Kokoro-82M, 4 threads (default) | 0.48 | Most natural of those tested (from published comparisons; we ran no listening test); 28 English voices |
| Kitten TTS nano | 0.11 | About 5× faster than Kokoro, but speaks slowly and needs a workaround on Windows |
| Piper | 0.03 | About 17× faster, but less natural, and its code is now GPL-3.0 |

### 8.8 Saved lessons

22 verified lesson plans are included, one per algorithm (112 steps in all). They are used by the tests, they work
without an API key, and they are what the Library plays. They were written during development by an AI assistant and
**accepted only after the verifier passed every one**, so their correctness does not depend on who wrote them.

| Family | Lessons (level) |
| --- | --- |
| Linear | Stack (beginner), Queue (intermediate), Deque (beginner), Linked list (beginner) |
| Trees | Binary search tree (intermediate), In-order traversal (beginner), Min-heap (intermediate) |
| Graphs | BFS (beginner), DFS (intermediate), Dijkstra (advanced), Topological sort (advanced) |
| Sorting | Bubble (beginner), Insertion (beginner), Selection (beginner), Merge (intermediate), Quick (advanced), Heap (advanced) |
| Searching | Linear search (beginner), Binary search (intermediate) |
| Hashing | Hash table (intermediate) |
| Dynamic programming | Fibonacci (beginner), Coin change (advanced) |

### 8.9 Turning away off-topic requests (topic gate)

Before the gate, "What is the capital of the Pakistan" spent **142.4 s** in the Plan stage before the planner refused
it. Through the real pipeline with the gate, the same request was refused in **1.46 s**, with no planning call.

We first timed the classifier prompt on both Gemini models, on an off-topic and an in-scope request. The main model,
`gemini-3.5-flash`, was overloaded that day: every call ended in a 503, a 429 or a 120 s timeout. The light model,
`gemini-3.5-flash-lite`, answered both correctly in 1.5 s and 9.6 s at its default reasoning, and in **0.8 s and
0.7 s at low reasoning effort**, which the gate now uses. Then we sent nine requests through `gate.check_topic`:

| # | Request | Expected | Gate | Tier | Time |
| --- | --- | --- | --- | --- | ---: |
| 1 | What is the capital of the Pakistan | refuse | refused | classifier | 11.1 s |
| 2 | Write me a poem about spring | refuse | refused | classifier | 2.0 s |
| 3 | Explain transformers in NLP | refuse | refused | classifier | 0.6 s |
| 4 | Who won the 2022 football world cup? | refuse | passed to the planner (503 from the server) | fallback | 9.3 s |
| 5 | How does a map app find the quickest route between two cities? | Dijkstra | Dijkstra | classifier | 10.2 s |
| 6 | How do I check if an item is in a sorted list quickly | binary search | binary search | classifier | 8.1 s |
| 7 | FIFO line at a bank, explain it | queue | queue | keyword | 0.0 s |
| 8 | How do I schedule tasks that depend on each other | topological sort | topological sort | classifier | 0.8 s |
| 9 | Explain bubble sort on 5 3 8 1 | bubble sort | bubble sort | keyword | 0.0 s |

- **Every answer the classifier gave was right**, including the three paraphrases that name no algorithm (5, 6, 8),
  which the gate passes on to the planner as that algorithm. Request 4 is not a wrong answer: the server returned
  503, and the gate let the request through, as designed; the planner then refuses it the slow way.
- **The times vary with the server's load, not with the request.** Of six repeated calls, three took 0.6 to 1.1 s, two
  waited about 9 s and one got a 503. After this run, quick calls keep the client's one automatic retry, since a busy
  server's 503 comes back in about a second, and the gate's timeout is 10 s.
- **Keyword topics cost nothing**: requests 7 and 9 were decided in under a millisecond, with no API call.

The run is small (nine requests on one day) and shows the design works; it is not a measurement of the classifier's
accuracy over many phrasings.

## 9. Limitations and future work

- **Scope.** 22 algorithms are supported. Other topics are refused with a message rather than explained badly. Adding
  one means writing a simulator class (and a picture, if none fits); the planner, verifier, quiz, API and Library
  need no change.
- **The topic gate trusts keywords.** A topic that contains an algorithm keyword passes without the classifier, so an
  off-topic request that happens to use one ("linear regression" matches linear search) still reaches the planner,
  which refuses it as slowly as before. When the light model is unavailable, the gate also lets requests through.
  In both cases the result is a slow refusal, never a wrong video.
- **Size.** At most 7 to 8 items or nodes per lesson, so the picture stays readable.
- **Narration checks are rule-based.** They catch wrong values and false statements about the facts they recognise, and
  every fact a plan declares, but not every wrong sentence, such as a wrong reason or a misleading analogy; 3% of
  our planted mistakes still pass (Section 8.4). A second model acting as a judge could be added, at the cost of time
  and of trusting that model.
- **Fixed conventions.** BFS and DFS take neighbours in alphabetical order and BST deletion uses the in-order
  successor. A course that teaches the predecessor would need a setting.
- **Voice.** Captions are timed by sentence, not by word, because no CPU voice engine we found gives word times. The
  default voice's phonemiser is GPL-3.0 (Section 2.5), and English is the only language.
- **Speed.** A new lesson takes about two to two and a half minutes on a six-core CPU, most of it speech synthesis
  and the quiz call. A GPU provider or a faster voice shortens this.
- **Free API limits.** Gemini's free tier allows about 20 requests a day per model, and a lesson needs at least two.
  The fallback model keeps the app working, but it is smaller; its quiz questions were rejected more often (the verifier
  caught every one). A paid key or another provider removes the limit.
- **Continuous integration.** The macOS and Linux runs of the workflow have not been seen yet (Section 8.2).
- **Language-model evidence is small.** The live runs use nine and two lessons; they show the design works but are not
  a statistical comparison of providers.

## 10. Use of generative AI tools

As the brief allows, we used an AI coding assistant (Claude Code) while building this project, in several sessions:
the course version, and then the ten milestones of the platform, which followed the written roadmap in
`docs/roadmap/milestones.md`. It drafted code, tests and documentation from our instructions, and we reviewed, ran and
tested the results. It also wrote the 22 saved lesson plans, each of which was accepted only after our verifier passed
it. The prompts that the application itself sends to the language model are in the code (`authoring/gate.py`,
`authoring/planner.py`, `authoring/quiz.py` and `authoring/revise.py`), and the prompts we gave the assistant are listed in
`docs/course/ai-prompts.md`.

## 11. Conclusion

DSA Explainer produces narrated, animated lessons on 22 data structures and algorithms, with quizzes whose answers
were computed and revisions that redraw only what changed, and it keeps them correct by never trusting the language
model with facts: every step is run on real data structures before anything is drawn, wrong plans are repaired with
the true state, and the video is drawn only from verified states. Requests outside the 22 algorithms are turned away
by a topic gate in about a second, before any lesson is planned. We measured the verifier rather than only claiming
it works: it catches 97% of 601 planted mistakes, and we state what still gets through. The speech and the animation
run locally on an ordinary laptop CPU, and only lesson planning and the quiz use a language model, which the learner
chooses, and can run on their own computer.
