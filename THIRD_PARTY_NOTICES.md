# Third-party notices

DSA Explainer's own code is under the [MIT licence](LICENSE). It is built on the work below. Packages are installed
by `pip` and `npm` from their own sources; the only third-party files kept in this repository are the Nunito font
(`backend/dsa_explainer/media/fonts/`, with its licence) and the frontend lock file. Versions are the ones the
project is tested with (`backend/requirements.txt`, `frontend/package-lock.json`); licences were read from each
package's metadata in November 2026.

## Models and assets

| Item | Used for | Licence | Where it comes from |
| --- | --- | --- | --- |
| Kokoro-82M weights and voices (`kokoro-v1.0.onnx`, `voices-v1.0.bin`) | Narration voice | Apache-2.0 | [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M), ONNX export from [kokoro-onnx releases](https://github.com/thewh1teagle/kokoro-onnx/releases); downloaded on first run into the data folder, not in git |
| Nunito (variable TTF) | Type in the videos | SIL Open Font License 1.1 (`media/fonts/OFL.txt`) | [google/fonts](https://github.com/google/fonts/tree/main/ofl/nunito) |
| Nunito and Nunito Sans web fonts (`@fontsource`) | Type in the web app | SIL Open Font License 1.1 | npm |
| Illustrations and icons in the web app | Pages | Original work, MIT with the code | this repository |

## Python packages (runtime)

| Package | Licence | Notes |
| --- | --- | --- |
| manim | MIT | Animation |
| manimpango | MIT | Text rendering (bundles Pango, LGPL) |
| pycairo | LGPL-2.1-only or MPL-1.1 | Manim's renderer |
| av (PyAV) | BSD-3-Clause | Reads clip lengths; its wheels bundle FFmpeg libraries (LGPL) |
| imageio-ffmpeg | BSD-2-Clause | Ships an `ffmpeg` executable used as a separate program to join clips; that binary has its own licence (see the imageio-ffmpeg documentation) |
| fastapi, pydantic | MIT | Local API, schemas |
| uvicorn, starlette, httpx, python-dotenv, numpy, scipy | BSD-3-Clause (numpy also includes 0BSD, MIT, Zlib, CC0 parts) | |
| openai | Apache-2.0 | Client for OpenAI-compatible language-model APIs |
| onnxruntime | MIT | Runs the voice model |
| kokoro-onnx | MIT | Kokoro inference |
| **phonemizer** | **GPL-3.0 or later** | Text to phonemes for Kokoro, required by kokoro-onnx |
| espeakng-loader | MIT | Ships the **espeak-ng** library and data (**GPL-3.0**), used by phonemizer |
| pillow | MIT-CMU | Images (through Manim) |
| svgelements, srt, moderngl, screeninfo, isosurfaces, rich, pydub, beautifulsoup4, attrs | MIT | Manim dependencies |
| skia-pathops, cloup, networkx | BSD-3-Clause | Manim dependencies |
| decorator | BSD-2-Clause | |
| mapbox-earcut | ISC | |
| tqdm | MPL-2.0 and MIT | |
| watchdog | Apache-2.0 | |
| audioop-lts | PSF-2.0 | Python 3.13 replacement for `audioop` |

**About the GPL components.** `phonemizer` and espeak-ng are installed as dependencies and called at run time;
DSA Explainer does not copy their code. Our source stays MIT. Anyone distributing a bundled binary that includes
them (for example a PyInstaller build) distributes a combined work and must follow the GPL for it. The path to a
GPL-free voice is described in [docs/research/voice-models.md](docs/research/voice-models.md#licence-position-espeak-ng).

## Python packages (development and tests)

| Package | Licence |
| --- | --- |
| pytest | MIT |
| hypothesis | MPL-2.0 |
| ruff | MIT |
| markdown | BSD-3-Clause |

## Web app (npm)

| Package | Licence |
| --- | --- |
| react, react-dom, react-router-dom, @tanstack/react-query | MIT |
| vite, @vitejs/plugin-react, eslint, typescript-eslint, eslint-plugin-react-hooks, globals | MIT |
| typescript | Apache-2.0 |
| @fontsource/nunito, @fontsource/nunito-sans | OFL-1.1 (the fonts), MIT (the packaging) |

## Services

The language model is a service the learner chooses (Gemini, OpenAI, Anthropic, Groq, OpenRouter, or a local
Ollama or LM Studio model) with their own key and under that provider's terms. Only lesson planning, quiz and
revision requests leave the machine.
