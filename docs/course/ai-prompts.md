# Prompts given to the AI coding assistant

The brief allows generative AI tools but asks that we can reproduce the prompts we used. This project was built with
**Claude Code** (Anthropic's coding assistant, desktop app) in several sessions: the course version in the first one,
then the open-source platform (Milestones 0 to 9, from the written roadmap in `docs/roadmap/milestones.md`), then a
polish session. These are our prompts to it, word for word (spelling mistakes included) and in order. The project
brief (`Project.pdf`) was attached to the first one.

## Session 1: the course version

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

## Sessions 2 and 3: the platform (Milestones 0 to 9)

The platform was built from the roadmap and vision documents in `docs/roadmap/` and the product and design notes in
`docs/design/`, in meaningful commits (one per milestone) on the branch `feat/open-source-platform`. **The prompts of
these sessions are not reproduced here** because they are not stored in the repository; add them from the Claude Code
session history if you need them. Each milestone's tasks, decisions and results are in `docs/roadmap/milestones.md`.

## Session 4: polish, release and the final report

The session started by pasting the previous session's summary of the five finished milestones. Then:

1. "In this session - we will do enhancements. Very first - bug I found on the settings page in the voice section no API route /api/voices getting this error as you can see in the image, please fix this" (with a screenshot)
2. "Yes, check"
3. "we will be doing small enhancements:just quicky do it I will verify it by myself. And just tell me in one line summary. That's it First: On the seetings page, voices section the voices dropdown menu showing voice their design not matching with the theme, make the dialog corners rounded and the scroll bar remvoe the top and bottom icon shapes only the scroll bar should be there redesign it as well to make it thinner match the design theme."
4. "Categories titles make them bold"
5. "Now let's come on the my lessons page - each lesson page the steps row showing horizontal scrolling remove it by having two rows of steps and below sections row quiz, verified etc that container showing vertical scrolling bar remove that"
6. "Next enhancement: verified section the metrics showing look at them text size is large that s going to the second line make sure always in one line" (with a screenshot)
7. "Next enhancement: the plan section the plan json scrolling bars not matching with the design"
8. A spoken request about the library page: move the difficulty levels along with the search, add a divider line after the category row, and give the algorithm cards more room.
9. "Next enhancement: the cards still looking tight spacing increase the height or use some other strategy"
10. "Next enhancement: still not looking the content should be gaped from the top heading title in the cards"
11. "Next enhancement: in the footer on the home page the logo icon shape the face shape remove it from there and place it above the cta line ready to see it move"
12. "Next enhancement: one bug in this face shape when eyes blinking happens there's a blurriness bug please fix this"
13. "Next enhancement: the artwork above the footer remove them"
14. "Next enhancement: Okey but the footer layering design also vanished as it was before. I want the footer design to the layering left and right or any other creative matching design theme footer"
15. "Look at this image - the layering color not sncyronizing with the bottom footer" (with a screenshot)
16. "Next enhancement: the start with favourite cards redesign they are looking tight spacing redesign their internal layout with easy, intermediate,advanced favourites"
17. "Next enhancement: remove this average time from the cards, the watch button and algo text link should always be on different line not on the same"
18. "Next enhancement: the text on the footer the links, headings and other looks very dull with the background green theme make them prominent changing their colors"
19. "Next enhancement: Now the most important in the hero section artwork as now our product is complete. This artwork is very important - current artwork not really showing the meaning, vision of the product so redesign the artwork for the hero section."
20. "Next enhancement: Not still not something attractive enough, accurate redesign again  can remove the logo face shape"
21. "Nope still Not like this version as well create something else"
22. "Okey this looks better but the arrows in the step 1 and step 2 not properly drawn please fix it after fixing commit all the changes in the branch and push this branch to remove after pushing merge this branch and push the main to the remote"
23. "yes perfect for the narrated icon use the same icon as in the message box with voice animated"
24. "Please launch the platform."
25. "Next enhancement: in the footer where this is written Made by Ahmed Javaid and Ammad Ashraf show my name as link to my portfolio https://ammad-ashraf.dev/ and for the ahmed javaid https://github.com/Ahmed-Javaid"
26. "commit and push this to main And one more thing I want to have a separate repo of the codebase to my personal github account instead of ahmed javaid. I want you to setup this for my account create a new repo on my account push to remote using github desktop. You have access of my machine"
27. "Yes, switch the links to my repo Just one quick thing all the next commits will go to my repo right ?"
28. "One quick thing about the submission - what I need to submit actually and the documentation, diagram and other artifacts are all those updates after after milestones updates in the project." We also pasted the course announcement that the report must follow the Complex Computing Problem (CCP) guidelines, with no change to the project idea or implementation.
29. "Yes, update all"

When the assistant asked, we chose the repository name `dsa-explainer` and a public repository.

## Session 5: the topic gate

1. A spoken request, with two screenshots of the Studio: "What is the capital of the Pakistan" took 142.4 s in the
   Plan stage before the refusal appeared. Could the query be filtered against the guardrails first, so it does not go
   on to the next stages and the message shows in the Plan phase, perhaps with a guardrail framework?
2. "Yes, build it"
3. "Okay, so before committing and pushing to both remotes, I want you to update all the required documentations as
   well to include this feature in the documentation as well. After that, meanwhile, I want you to restart the server
   so I can just evaluate the gates, and you can update the documentation. After that, commit and push to the both
   remotes."

## The prompts inside the application

The prompts that the **application** sends to its own language model at run time are part of the code:

- topic gate (is the request about a supported algorithm?): `SYSTEM_PROMPT` in `backend/dsa_explainer/authoring/gate.py`
- lesson planning: `SYSTEM_PROMPT` in `backend/dsa_explainer/authoring/planner.py`
- quiz questions: `PROMPT` in `backend/dsa_explainer/authoring/quiz.py`
- rewrite revisions: `PROMPT` in `backend/dsa_explainer/authoring/revise.py`
