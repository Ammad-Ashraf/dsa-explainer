# Voice models for DSA Explainer

*Research for Milestone 4, November 2026. Measurements were taken on the development laptop described below;
the scripts that produced them are in the repository, so anyone can repeat them on their own machine.*

## What the narration voice must do

| Requirement | Why |
| --- | --- |
| Runs **locally**, on a CPU | A requirement of the project: the learner's machine speaks; nothing is sent to a speech API. |
| Faster than real time on a laptop | Voicing a lesson (about 2 minutes of speech) must not be the slow stage. |
| Open weights with a licence that allows redistribution and commercial use | The project is MIT-licensed open source. |
| Works on Windows, macOS and Linux with `pip install` | No compilers, no system packages for a first run. |
| Clear English, several voices | Lessons are in English; learners like to choose a voice. |
| Timings (word or sentence) | For captions, and to keep pictures in step with the words. |
| Correct reading of the field's vocabulary | "deque", "BFS", "O(n log n)", "a[i]". |

## Candidates

Licences are those of the code and of the weights, which often differ. "CPU speed" is the real-time factor (RTF):
seconds of computing per second of audio, so below 1 is faster than real time. Figures marked *measured* are ours
(next section); the others are the authors' claims, on their hardware.

| Model | Size | Code licence | Weights licence | CPU speed | Timestamps | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| **Kokoro-82M** via `kokoro-onnx` | 82M, 326 MB ONNX | MIT (`kokoro-onnx`); phonemiser `phonemizer` GPL-3.0+ with espeak-ng GPL-3.0 | Apache-2.0 | **RTF 0.48 to 0.51, measured** | Phoneme durations only from exports that output them; the released `kokoro-v1.0.onnx` does not (checked: its only output is `audio`) | 54 voices, 28 of them English (US and UK). The voice of the course version. |
| **Piper** (`piper-tts`, OHF-Voice/piper1-gpl) | 15 to 75M per voice (VITS) | GPL-3.0 since the move to `piper1-gpl` (the old `rhasspy/piper` was MIT and is archived) | Per voice: many CC-BY or CC0; *lessac* carries the Blizzard licence's restrictions | **RTF 0.03, measured** | No | 50+ languages, built for a Raspberry Pi; less natural than Kokoro in published comparisons. |
| **Kitten TTS nano** (KittenML) | 15M, 25 to 56 MB | Apache-2.0 | Apache-2.0 tag on the 0.x nano weights (check the model card; KittenTTS 2 uses a non-open community licence) | **RTF 0.11, measured** | No | Smallest download; 8 voices; also phonemises with espeak-ng (GPL). |
| **Pocket TTS** (Kyutai) | 100M | MIT | CC-BY-4.0 | about 6x real time on 2 cores of an Apple M4 (authors) | Not exposed | Voice cloning from a short sample; needs PyTorch. |
| **Supertonic** (Supertone) | 66M (v1) to 99M (v3), ONNX | MIT | OpenRAIL-M (use restrictions) | RTF about 0.02 on an M4 Pro CPU (authors) | No | Very fast, ONNX Runtime only, 31 languages in v3; the weights licence is not OSI-open. |
| **Chatterbox** (Resemble AI) | Nano 110M, Turbo 350M | MIT | MIT | Nano about 3x real time on 8 CPU threads (authors); Turbo is meant for GPUs | No | Expressive, cloning; PyTorch. |
| **NeuTTS Air** (Neuphonic) | 0.5B (GGUF) | Apache-2.0 | Apache-2.0 | Runs through llama.cpp on CPU (not measured here) | No | Cloning; no PyTorch needed. |
| XTTS-v2, F5-TTS, Fish Speech | 0.3 to 1B | various | **Non-commercial** | GPU | some | Excluded: the weights cannot be redistributed with an MIT project for any use. |
| Qwen3-TTS, Dia, Orpheus | 0.6 to 3B | Apache-2.0 | Apache-2.0 | GPU | some | Excluded for now: too slow without a GPU, which most learners do not have. |

Sources: the projects' own pages and model cards
([Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M), [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx),
[piper1-gpl](https://github.com/OHF-Voice/piper1-gpl), [piper-voices](https://huggingface.co/rhasspy/piper-voices),
[KittenTTS](https://github.com/KittenML/KittenTTS), [Pocket TTS](https://github.com/kyutai-labs/pocket-tts),
[Supertonic](https://huggingface.co/Supertone/supertonic), [Chatterbox](https://github.com/resemble-ai/chatterbox)),
and surveys of local TTS in 2026 ([pinggy](https://pinggy.io/blog/best_open_source_self_hosted_text_to_speech_models/),
[yaps](https://www.yaps.ai/blog/best-local-tts-models)). Licences change: check the model card before adding an engine.

## Measurements on this machine

Laptop: AMD Ryzen 5 4500U (6 cores, 6 threads, 2020 mobile CPU), Windows 11, Python 3.13, ONNX Runtime 1.31.
Text: the first step narration of six saved lessons, 186 words, about 52 seconds of speech, spoken sentence by
sentence (as the app does). One warm-up sentence first; "load" includes reading the model.

Kokoro-82M (`python backend/scripts/voice_benchmark.py`), by ONNX Runtime thread count:

| Threads | Load + first sentence | Audio | RTF overall | RTF median per sentence |
| --- | --- | --- | --- | --- |
| default (ONNX Runtime picks: one per core) | 2.9 s | 52.0 s | 0.51 | 0.51 |
| 1 | 3.2 s | 52.0 s | 1.04 | 1.05 |
| 2 | 2.2 s | 52.0 s | 0.65 | 0.66 |
| 4 | 2.0 s | 52.0 s | **0.48** | 0.48 |
| 6 | 1.9 s | 52.0 s | 0.50 | 0.50 |

Other engines (`docs/research/bench_other_engines.py`, run in a separate virtual environment):

| Engine | Load + first sentence | Audio | RTF |
| --- | --- | --- | --- |
| Kokoro-82M (default threads, for comparison) | 2.9 s | 52.0 s | 0.51 |
| Piper 1.8, `en-us-lessac-medium` voice | 0.1 s | 50.7 s | **0.03** |
| Kitten TTS 0.1.3, `kitten-tts-nano-0.1`, voice `expr-voice-2-f` | 2.5 s | 86.8 s | 0.11 |

Piper is about seventeen times faster than Kokoro and Kitten about five times. We did not run a listening test;
published comparisons rate both below Kokoro for naturalness, and Kitten's nano voice speaks slowly: the same text took 87
seconds of audio instead of 52. Kitten needed `PHONEMIZER_ESPEAK_LIBRARY` pointed at the espeak-ng library that
`espeakng-loader` ships before it would run on Windows. The Piper voice came from the `rhasspy/piper` GitHub
release, because the Hugging Face download ran at about 50 kB/s here.

Reading the numbers: Kokoro speaks a two-minute lesson in about a minute on a five-year-old laptop CPU, which is
already less than the drawing takes (Milestone 8 measures the whole pipeline). Doubling the threads past two buys
little, because the model is small; four threads are as fast as six. That matters because the voice runs while
the drawing processes use the other cores (see [Milestone 8](../roadmap/milestones.md)).

## Decision

1. **Kokoro-82M stays the default engine.** Among models with open, redistributable weights it is the best
   sounding one that runs well faster than real time on an ordinary CPU, and it installs with `pip` on all three
   systems. Nothing newer we found beats it on all of quality, speed and licence at once: Supertonic is faster but
   its weights are OpenRAIL-M; Pocket TTS and Chatterbox are larger and need PyTorch; Piper and Kitten are much faster
   but less natural, and Piper's code is now GPL.
2. **Engines are pluggable** (`backend/dsa_explainer/media/voices/`). An engine implements `voices()` and
   `synthesize(sentence, voice, speed)`; sentence splitting, the lexicon, caching, timings and captions are shared.
   The next engines worth adding are Supertonic (speed, multilingual; licence noted in the app) and Pocket TTS
   (cloning), each as an optional install.
3. **Timings by sentence, exactly.** None of the CPU candidates gives word timestamps from its standard runtime,
   and the released Kokoro ONNX file has no duration output. The app therefore synthesises each sentence on its
   own and joins them with a 0.25 s pause (what Kokoro inserts itself), so every sentence's start and end in the
   audio is exact. Captions (WebVTT) are cut from these spans; a long sentence is split at commas, its pieces timed
   by their share of the letters. Forced alignment (for example with a CTC aligner) could add word timings later
   without changing the engines.
4. **A pronunciation lexicon** (`media/voices/lexicon.py`) rewrites what is spoken, not what is shown: acronyms
   (BFS, BST, LIFO), notation (O(n log n), a[i], push(7), ->, <=), and words voices get wrong (deque, enqueue,
   Dijkstra). It has its own tests and a version number in the audio cache key.

## Licence position (espeak-ng)

DSA Explainer's code is MIT. `kokoro-onnx` (MIT) turns text into phonemes with the `phonemizer` package
(GPL-3.0 or later), which drives espeak-ng (GPL-3.0) through `espeakng-loader` (MIT, which ships the espeak-ng
library). These are ordinary dependencies that `pip` installs next to ours; we do not copy their code into the
repository. Our position:

- The MIT licence of our source code stands: it is a separate work that calls a GPL library at run time, which
  we disclose in [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md).
- Anyone who **distributes a bundled binary** that contains these packages (an installer made with PyInstaller,
  say) distributes a combined work and must follow the GPL for it, including offering the source.
- The path to a fully non-GPL voice exists and is recorded for later: `kokoro-onnx` accepts phonemes directly
  (`is_phonemes=True`), so a permissive grapheme-to-phoneme converter such as `misaki` (Apache-2.0, used by the
  official Kokoro package) without its espeak fallback could replace `phonemizer`. Today `kokoro-onnx` imports
  `phonemizer` unconditionally, so this needs either an upstream option or a small engine of our own around the
  ONNX model.

## How to repeat the measurements

```bash
python backend/scripts/voice_benchmark.py --threads 0 1 2 4 6
```

For the other engines, create a separate virtual environment as described at the top of
`docs/research/bench_other_engines.py` (they are not dependencies of DSA Explainer).
