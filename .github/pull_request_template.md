## What and why

<!-- What does this change, and why? Link the issue if there is one. -->

## Checklist

- [ ] Nothing reaches a video without the verifier checking it (the one rule in CONTRIBUTING.md)
- [ ] Tests added for what this adds; `python -m pytest backend -q` passes
- [ ] `ruff check .` passes
- [ ] Web app changes: `npm test` and `npm run build` pass in `frontend/`, and I looked at the pages
- [ ] Picture changes: I watched a rendered clip, bumped `RENDER_VERSION`, and approved the golden layouts
- [ ] New dependency, model or asset: its licence is in THIRD_PARTY_NOTICES.md
