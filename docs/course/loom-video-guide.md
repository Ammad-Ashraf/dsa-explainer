# Loom video guide

The brief asks for **a 2 to 3 minute Loom video of the product, including a quick demo**. This guide is a ready
script: what to show, what to say, and what to do if something goes wrong. It runs about 2 minutes 50 seconds. Pause
Loom while the first scene is being made (step 2) so the waiting does not count.

## Before you record (about 10 minutes)

1. **Start the app.** In a terminal in the `dsa-explainer` folder:
   ```bash
   .venv\Scripts\activate
   dsa-explainer
   ```
   The first run downloads the voice model (about 350 MB); after that it starts at once, opens
   http://127.0.0.1:8000 and shows the home page. If you have not built the web app yet:
   `cd frontend && npm ci && npm run build`.
2. **Check the language model.** Open **Settings**, pick your provider (for example Google Gemini), paste the key if
   it is not saved, and click the test button. It should say the connection works.
3. **Do one practice run** of the demo topic below, so you know it works today and roughly how long it takes (the
   first scene plays after about one minute and the whole video is ready after two to two and a half). Mind the free
   Gemini allowance: about 20 requests a day for the main model, and each new lesson uses 2 or more. When it runs
   out, the app switches to Gemini 3.5 Flash-Lite by itself, and the **Verified** tab names the model it used. The
   allowance resets at midnight Pacific time (1 pm in Pakistan).
4. **Prepare the screen.** Put the browser in full screen (F11) at 100% zoom, close other tabs, and turn on Do Not
   Disturb in Windows so no notifications pop up.
5. **Open two extra things:** `docs/course/architecture.png` in an image viewer, and a second terminal in the
   `dsa-explainer` folder with the virtual environment activated. Run `python -m pytest backend -q` in it once
   beforehand (about two minutes, 303 tests) and keep the finished output on screen.
6. **Loom settings:** "Screen and camera", full screen, 1080p, your microphone selected (check the level). Put the
   camera bubble at the bottom left, where it does not cover the video player.
7. **Decide who speaks when.** For example, Ahmed does the first four rows and Ammad does the rest.

## Script

| Time | Show | Say (roughly) |
| --- | --- | --- |
| 0:00 to 0:15 | The home page | "Hi, we're Ahmed Javaid and Ammad Ashraf, and this is DSA Explainer, our NLP project. You type a data-structures topic, and it makes a narrated, animated video lesson with a quiz. Every step is checked by running the real data structure before anything is drawn." |
| 0:15 to 0:35 | Click **Make a lesson**. Type **Insert 8, 3, 10, 1, 6, 14 into a BST, then delete 3**, choose **Intermediate** and **Draft**, click **Make my lesson**. Point at the pipeline rail as the stages run. Pause Loom when "Plan" is running and resume when the first scene appears. | "The language model you choose writes the lesson as a JSON plan: the operations, the state after each one, the facts the narration states. Our verifier runs every step on a real binary search tree. If the model gets a state wrong, the plan goes back to it with the true state. Notice the quiz is written while the scenes are drawn, and you can watch the first scene before the video is finished." |
| 0:35 to 1:20 | Play the video. Point at the pseudocode card with the highlighted lines and at the facts strip above the picture. Click ahead to the step that deletes 3, then to the quiz. Pick a wrong answer to show the reason. | "The voice runs locally on the CPU, and Manim draws each scene from the verified states. The pseudocode lines that ran are highlighted, and the strip shows the simulator's counts. Deleting 3, which has two children, replaces it with its in-order successor, 6. The quiz answers are computed, and the wrong options come from real mistakes, so it tells you which mistake you made." |
| 1:20 to 1:45 | Open the **Verified** tab, then **Plan** for a second. | "Here you see what was checked, whether any plan was sent back and why, and where the time went: the quiz overlaps the drawing. This is the plan the model wrote, after it was verified." |
| 1:45 to 2:10 | **Change it** tab: type **slow down step 2** and press Enter. When it finishes, point out how few scenes were drawn again. | "We can change any part of the lesson. Only the changed scene is drawn again, and the rest comes from the cache, so the change takes about ten seconds." |
| 2:10 to 2:30 | **Library**: open **Dijkstra** and pick an operation to show its pseudocode lines. Then **Settings**: show the provider list and the voice picker, and click **Preview voice**. | "There are 22 algorithms with ready-made lessons that need no key. You can bring a key for Gemini, OpenAI, Claude, Groq or OpenRouter, or run a model locally with Ollama. The voice is Kokoro, and you can pick and preview other voices." |
| 2:30 to 2:50 | `docs/course/architecture.png`, then the terminal with **303 passed**. | "The language model only plans and writes text. The verifier is plain Python, and it catches 97% of 601 mistakes we planted in the saved lessons. The voice, the animation and the video joining run locally. We have 303 tests. The code, the report and this video are in our repository. Thanks for watching." |

If you have time left, show a refusal: type **What is the capital of Pakistan** and click **Make my lesson**. The
topic gate stops it in the Plan stage in about a second and explains which topics are supported, instead of making an
unchecked video. (It used to take over two minutes, because the planner itself had to refuse it.)

## If something goes wrong

- **The API is slow or returns an error** (503 means busy, 429 means rate limit). Wait a minute and try again, or open
  the **Library**, choose an algorithm and click **Watch**. Say it is a saved lesson that went through the same
  verifier.
- **The verifier sends a plan back.** That is a good thing to show. The **Verified** tab will list the reason.
- **No voice model yet.** Run `dsa-explainer download-models` once and start again.
- **You stumble.** Stop and re-record that part. Loom can trim the start and the end.

## After recording

1. Trim the start and end in Loom, and give it a title such as "DSA Explainer: NLP Project (22i-2530, 22i-2470)".
2. Set sharing to "Anyone with the link can view".
3. Paste the link into `README.md` (the "Demo video" line near the end) and `docs/course/report.md` (the "Demo
   video" row). Then rebuild the PDF with `python backend/scripts/build_report.py`, commit, and push.
