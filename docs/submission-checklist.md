# Submission checklist

Deadline: **30 November 2026, 11:59 pm**. Submit one private GitHub repository link on Google Classroom, or a .zip with
the same contents. No late submissions.

## Already done

- [x] Full code, documentation and tests in the repository (35 tests pass; a fresh clone installs and runs)
- [x] System architecture diagram: `docs/architecture.png` (also in the README and the report)
- [x] Report: `docs/report.md`, printed to `docs/report.pdf`
- [x] README with the project, models and APIs, what runs locally, and the architecture
- [x] Live evaluation with Gemini: `docs/live-eval.md`
- [x] Loom script: `docs/loom-video-guide.md`
- [x] Prompts given to the AI assistant: `docs/ai-prompts.md`
- [x] The API key is kept out of git (`.env` and `GeminiAPIKey.txt` are ignored)

## Needs your input

1. **Check the group details** in `README.md` and `docs/report.md`: Ahmed Javaid (22i-2530) and Ammad Ashraf
   (22i-2470).
2. **Record the Loom video** with `docs/loom-video-guide.md` (2 to 3 minutes). Set sharing to "Anyone with the link".
3. **Paste the Loom link** into `README.md` (the "Demo video" line) and `docs/report.md` (the "Demo video" row).
4. **Give people access to the private repository.** The code is pushed to
   https://github.com/Ahmed-Javaid/NLP-Project-2026 (private). Add your partner, and the instructor or TA if the
   course needs that, under Settings > Collaborators.
5. **Rebuild the PDF, commit and push** after the edits above:
   ```bash
   python scripts/build_report.py
   git add -A
   git commit -m "Add demo video and repository links"
   git push
   ```
6. **Or submit a .zip instead of the link.** This packs exactly what is committed (no `.env`, no key file, no models):
   ```bash
   git archive --format=zip --prefix=NLP-Project_22i-2530_22i-2470/ -o ../NLP-Project_22i-2530_Ahmed-Javaid_22i-2470_Ammad-Ashraf.zip HEAD
   ```
7. **Submit on Google Classroom** before the deadline.

## For the viva

- Read `docs/report.md` sections 3 and 4. They explain every module in the order the data flows.
- Be ready to explain the three ideas that matter most:
  - the verifier runs every step on real data structures and sends errors back with the true state;
  - one `morph` function animates every operation by matching shape keys between the before and after pictures;
  - clips are cached by their content, so a revision redraws only the changed scenes.
- Know where the prompts are: `docs/ai-prompts.md` (yours) and the `PROMPT` constants in `planner.py`, `quiz.py` and
  `revise.py` (the app's).
- Run `python -m pytest` once before the viva. To show the verifier at work, open `tests/test_verifier.py`: each test
  plants one mistake.
