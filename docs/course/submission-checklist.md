# Submission checklist

Deadline: **30 November 2026, 11:59 pm**. Submit one private GitHub repository link on Google Classroom, or a .zip with
the same contents. No late submissions.

## What you submit

- The repository (or the .zip): the code, the tests, the README, the report, the architecture diagram, the live
  evaluation, the prompts file and the Loom guide, all under `docs/course/` except the code and the README.
- The report as `docs/course/report.md` and the printed `docs/course/report.pdf`. It follows the Complex Computing
  Problem guidelines: Section 2 has the Problem Statement, Complexity Drivers, Design Justification, Trade-off
  Analysis and Societal and Ethical Impact, and the rest has the module descriptions, setup and technical details.
- The Loom video (2 to 3 minutes), linked from the README and the report.

## Already done

- [x] Full code, documentation and tests in the repository (303 backend tests and 8 web-app tests pass, `ruff` is
      clean; run `python -m pytest backend -q` and `cd frontend && npm test`)
- [x] System architecture diagram: `docs/course/architecture.png`, redrawn for the finished project (React app, local
      API server, pluggable voice, quiz written in parallel); regenerate with `python backend/scripts/make_diagram.py`
- [x] Report: `docs/course/report.md`, updated to the finished project (22 algorithms, the milestones, the mutation
      tests, the JSON-mode and latency measurements), printed to `docs/course/report.pdf`
- [x] CCP guidelines: report Section 2 (2.1 to 2.5) has the five required parts
- [x] README with the project, the quick start, how it works, performance, development and licence
- [x] Live evaluation with Gemini: `docs/course/live-eval.md` (the fixed course run), plus the later evaluations in
      `docs/research/`
- [x] Loom script: `docs/course/loom-video-guide.md`, for the current app
- [x] Prompts given to the AI assistant: `docs/course/ai-prompts.md`
- [x] API keys are kept out of git (`.env`, `settings.json` and `GeminiAPIKey.txt` are ignored; the history was checked)

## Needs your input

1. **Check the group details** in `README.md` and `docs/course/report.md`: Ahmed Javaid (22i-2530) and Ammad Ashraf
   (22i-2470).
2. **Record the Loom video** with `docs/course/loom-video-guide.md` (2 to 3 minutes). Set sharing to "Anyone with the
   link".
3. **Paste the Loom link** into `README.md` (the "Demo video" line at the end) and `docs/course/report.md` (the "Demo
   video" row).
4. **Decide how the repository is shared.** The code is at https://github.com/Ammad-Ashraf/dsa-explainer, which is
   currently **public**. The brief asks for a private repository, so either make it private (Settings, then Danger
   Zone, then Change visibility) and add your partner and the instructor or TA under Settings > Collaborators, or
   submit the .zip (step 7).
5. **Add the earlier prompts to `docs/course/ai-prompts.md`** if you still have them. It lists the first session and
   the polish session word for word, but the sessions that built Milestones 0 to 9 are only described, because their
   prompts are not in the repository.
6. **Check the GitHub Actions tab.** The workflow in `.github/workflows/ci.yml` had not run on GitHub when the report
   was written. If a macOS or Linux job fails, fix it before you submit (the report says it is untested).
7. **Rebuild the PDF, commit and push** after the edits above (needs Edge or Chrome installed):
   ```bash
   python backend/scripts/build_report.py
   git add -A
   git commit -m "Add demo video and repository links"
   git push
   ```
8. **Or submit a .zip instead of the link.** This packs exactly what is committed (no `.env`, no key file, no models):
   ```bash
   git archive --format=zip --prefix=NLP-Project_22i-2530_22i-2470/ -o ../NLP-Project_22i-2530_Ahmed-Javaid_22i-2470_Ammad-Ashraf.zip HEAD
   ```
9. **Submit on Google Classroom** before the deadline.

## For the viva

- Read `docs/course/report.md` Sections 2, 4, 5 and 8.4. Section 2 is the Complex Computing Problem analysis, Sections
  4 and 5 explain every module in the order the data flows, and Section 8.4 explains how we measured the verifier.
- Be ready to explain the four ideas that matter most:
  - the verifier runs every step on real data structures and sends errors back with the true state, and we measured it:
    it catches 97% of 601 planted mistakes;
  - every algorithm is one class in a registry that the planner, verifier, quiz, renderer and web app all read from, so
    adding one needs no change elsewhere;
  - one `morph` function animates every operation by matching shape keys between the before and after pictures, and
    clips are cached by their content, so a revision redraws only the changed scenes;
  - the quiz is written while the scenes are voiced and drawn, which cut a build from about 200 s to about 140 s.
- Know the honest limits: narration checks are rule-based (3% of planted mistakes still pass), captions are timed by
  sentence, the default voice's phonemiser is GPL-3.0, and the macOS and Linux CI runs were not yet seen.
- Know where the prompts are: `docs/course/ai-prompts.md` (yours) and the prompt constants in `authoring/gate.py`,
  `authoring/planner.py`, `authoring/quiz.py` and `authoring/revise.py` (the app's).
- Be ready to explain the topic gate: keywords first, then a one-second classifier call to a lighter model, and it
  fails open, so an outage means a slow refusal by the planner, never a blocked topic or a wrong video
  (report Sections 5.2 and 8.9).
- Run `python -m pytest backend -q` once before the viva. To show the verifier at work, open
  `backend/tests/test_verifier.py` (each test plants one mistake) or run `python backend/scripts/mutation_report.py`.
