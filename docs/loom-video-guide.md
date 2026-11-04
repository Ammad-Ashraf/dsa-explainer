# Loom video guide

The brief asks for **a 2 to 3 minute Loom video of the product, including a quick demo**. This guide is a ready
script: what to show, what to say, and what to do if something goes wrong. It runs about 2 minutes 45 seconds. Pause
Loom while the video is being made (step 2) so the waiting does not count.

## Before you record (about 10 minutes)

1. **Start the app.** In a terminal in the `dsa-explainer` folder:
   ```bash
   .venv\Scripts\activate
   python -m dsa_explainer.llm
   python app.py
   ```
   The first command should print `{"ok": true}`. The second opens http://127.0.0.1:7860 in your browser.
2. **Do one practice run** of the demo topic below, so you know it works today and roughly how long it takes
   (about 1.5 minutes). Mind the free Gemini allowance: about 20 requests a day for the main model, and each new
   lesson uses 2 or more. When it runs out, the app switches to Gemini 3.5 Flash-Lite by itself, and the report under
   the video names the model it used. The allowance resets at midnight Pacific time (1 pm in Pakistan).
3. **Prepare the screen.** Put the browser in full screen (F11) at 100% zoom, close other tabs, and turn on Do Not
   Disturb in Windows so no notifications pop up.
4. **Open two extra things:** `docs/architecture.png` in an image viewer, and a second terminal in the
   `dsa-explainer` folder with the virtual environment activated, ready to run `python -m pytest`.
5. **Loom settings:** "Screen and camera", full screen, 1080p, your microphone selected (check the level). Put the
   camera bubble at the bottom left, where it does not cover the video player.
6. **Decide who speaks when.** For example, Ahmed does sections 1 to 4 and Ammad does 5 and 6.

## Script

| Time | Show | Say (roughly) |
| --- | --- | --- |
| 0:00 to 0:15 | The app's home page | "Hi, we're Ahmed Javaid and Ammad Ashraf, and this is DSA Explainer, our NLP project. You type a data-structures topic, and it makes a narrated, animated video lesson with a quiz. Every step is checked by running the real data structure before anything is drawn." |
| 0:15 to 0:35 | Type **Insert 8, 3, 10, 1, 6, 14 into a BST, then delete 3**, choose **intermediate**, click **Make video**. Wait until the progress bar shows "Planning the lesson". | "Gemini writes the lesson as a JSON plan: the operations, the state after each one, and the narration. Our verifier runs every step on a real binary search tree. If the model gets a state wrong, the plan goes back to it with the true state." **Pause Loom now** and resume when the video appears. |
| 0:35 to 1:15 | Play the start of the video. Then click ahead to the step that deletes 3, and then to the end for the quiz answer. | "The voice is Kokoro, running locally on our CPU, and Manim draws each scene. Inserting follows one path from the root, highlighted in blue. Deleting 3, which has two children, replaces it with its in-order successor, 6. At the end there is a quiz, and every answer was checked by running the operations." |
| 1:15 to 1:35 | Scroll to the report under the video: checks passed, any plans sent back, clips, time. Open **Lesson plan** for a second. | "Here you can see how many checks passed, and if the verifier sent a plan back, why. This is the plan the model wrote, after it was verified." |
| 1:35 to 2:00 | In **Change part of the video**, type **slow down step 2** and press Enter. When it finishes, point at "1 drawn now, 9 reused". | "We can change any part of the lesson. Only the changed scene is drawn again, and the rest comes from the cache, so the change takes about ten seconds." |
| 2:00 to 2:25 | `docs/architecture.png` | "The language model only plans and writes text. The verifier is plain Python. The voice, the animation and the video joining all run locally, and the clips are drawn in parallel while the narration is being spoken." |
| 2:25 to 2:45 | The terminal: run `python -m pytest` and show "35 passed". | "We have 35 tests, including ones that plant mistakes and check that the verifier catches them. The code, the report and this video are in our repository. Thanks for watching." |

If you have time left, show a refusal: type **Explain heap sort** and click Make video. The app explains that only
the five supported structures are covered instead of making an unchecked video.

## If something goes wrong

- **The API is slow or returns an error** (503 means busy, 429 means rate limit). Wait a minute and try again, or
  open **No API key? Make a video from a saved lesson plan**, choose `bst` and click the button. Say it is a saved plan
  that went through the same verifier.
- **The verifier sends a plan back.** That is a good thing to show. The report will list the reason.
- **You stumble.** Stop and re-record that part. Loom can trim the start and the end.

## After recording

1. Trim the start and end in Loom, and give it a title such as "DSA Explainer: NLP Project (22i-2530, 22i-2470)".
2. Set sharing to "Anyone with the link can view".
3. Paste the link into `README.md` (the "Demo video" line) and `docs/report.md` (the "Demo video" row). Then rebuild
   the PDF with `python scripts/build_report.py`, commit, and push.
