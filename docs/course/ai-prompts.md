# Prompts given to the AI coding assistant

The brief allows generative AI tools but asks that we can reproduce the prompts we used. This project was built in
one session with **Claude Code** (Anthropic's coding assistant, desktop app). These are our prompts to it, word for
word and in order. The project brief (`Project.pdf`) was attached to the first one.

1. "What is the best to do amongst this"
2. "explain each project and which looks good on a cv"
3. "career intelligence sounds fun"
4. "how long would each project take for you to bui;d"
5. "so DSA explainer is the easiest to make an dexplain?"
6. "how is DSA the easiest, would we need api or local compute power?"
7. "Start making it"
8. "Yes, commit it"
9. "what API keys do you need?"
10. "Yes, commit it"
11. "is it completely done?"
12. "make the report, run the tests, and make a loom video guide aswell. Get it ready to the its just our inputs."
13. "when does push it https://github.com/Ahmed-Javaid/NLP-Project-2026.git"
14. "What is left to do"
15. We pasted the course announcement that the report must follow the Complex Computing Problem (CCP) guidelines
    (problem statement, complexity drivers, design justification, trade-off analysis, and societal and ethical
    impact), with no change to the project itself. This produced Section 2 of the report.

When the assistant asked how commits should be credited, we chose: "Ammad co-author only". When it pointed out that
the GitHub repository was public, we chose: "Make it private, then push".

The prompts that the **application** sends to its own language model at run time are part of the code:

- lesson planning: `SYSTEM_PROMPT` in `dsa_explainer/planner.py`
- quiz questions: `PROMPT` in `dsa_explainer/quiz.py`
- rewrite revisions: `PROMPT` in `dsa_explainer/revise.py`
