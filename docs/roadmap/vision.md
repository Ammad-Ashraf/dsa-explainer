# Vision: DSA Explainer as an open-source platform

*Ideas from Ammad Ashraf, recorded 20 November 2026. Work happens on the `feat/open-source-platform` branch.*
*The plan that turns these ideas into work is in [milestones.md](milestones.md).*

## Where we are

DSA Explainer was built for Project 1 of our NLP course (implementation by Ahmed Javaid). The course version is
complete and is submitted from `main`. Its engineering pipeline is sound and more than enough for the course: a
language model plans the lesson, a verifier runs every step on a real data structure, a local voice model narrates,
Manim animates, and the learner gets a video with a quiz and can ask for changes.

The next goal is to make it an **open-source platform and launch it properly**, improving it from several angles:
usability, latency, the range of algorithms, the quality of the animations, and the engineering pipeline itself.

## Constraints that stay

- **Local-first.** The voice model must run locally (a requirement of the project). The backend is therefore not
  deployed, and so there is no point deploying the frontend either. Everything runs on the learner's own machine.
- **Correctness first.** The language model never has the last word on facts, and the renderer only draws what the
  verifier has checked. A wrong video is worse than no video. Every enhancement keeps this rule.
- **Open source.** The code, the setup and the documentation must work for people outside our team.

## 1. Frontend

1. **Migrate to a modern stack.** The current interface is Gradio, a Python UI framework. Replace it completely with
   a **React** web app.
2. **Layout and sections.** Model the app's pages, sections and content on a **reference web app**. Analyse its
   pages, what each section contains, and how content is organised, then design our layout from that.
   Reference: [visualizedsa.com](https://visualizedsa.com/), for the sections only.
3. **Design system.** Take the design system of a **reference website** (design tokens, colours, typography, spacing,
   components, motion, graphics) and build our app with it. Reference:
   [design-system.md](../design/design-system.md).
4. **Content and product decisions** (copy, the exact layout, where the video, the pipeline progress and every
   feature appear) are left to the implementation; see [product.md](../design/product.md).
5. **Autonomy.** The platform is completed milestone by milestone with minimal intervention, asking only when
   something is genuinely needed from Ammad.

## 2. Language model: bring your own key

- Today the lesson planner and the quiz writer call a third-party LLM API using one key from `.env` (currently a
  free-tier Gemini key).
- **The user should be able to give their own API key** (and choose their provider), and the app uses it.
- The planner and the quiz writer should be built in a **scalable, provider-independent** way, so new providers and
  models are easy to add.

## 3. Voice

- The local voice model works, and the synchronisation of audio with the animation frames works perfectly. Keep that.
- **Research the latest advances in voice models** (Hugging Face and other platforms) so the project uses the most
  recent models and ecosystem, and enhance the voice part of the pipeline with what we find.

## 4. More data structures and algorithms

- Add many more data structures and algorithms, **in a structured way**, each with its own **simulator** and
  **renderer**.
- Use the latest Claude models to create **detailed saved lesson plans** for these algorithms ahead of time, so
  learners get high-quality lessons immediately.

## 5. Better animations

- Improve the simulators and renderers so the videos are **more meaningful and more animated**, while staying
  **provably correct**: everything on screen must still come from the verified simulation.

## 6. Verification and the rest of the pipeline

- Enhance the verification step, and look for any other improvement in the engineering pipeline.

## 7. Repository

- Reorganise the repository for the platform and do all the work on the new branch (done in Milestone 0).

## Decisions

The open questions raised when these ideas were first written down (references, licence, name, who writes the saved
plans, where keys live, the course submission) are decided in [milestones.md](milestones.md#decisions).
