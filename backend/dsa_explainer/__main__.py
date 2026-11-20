"""Command line (installed as `dsa-explainer`; from a checkout, `python -m dsa_explainer` inside backend/).

    dsa-explainer                                  download the voice model if needed, serve the app, open it
    dsa-explainer serve [--port 8000] [--open] [--no-download]
    dsa-explainer download-models                  just fetch the voice model (about 350 MB)
    dsa-explainer "how does a queue work" --level beginner
    dsa-explainer --file dsa_explainer/plans/stack.json --quality standard
    dsa-explainer --version
"""

from __future__ import annotations

import argparse
import sys

from . import config


def ensure_models() -> None:
    """Fetch the voice model on first run. The app still starts without it (saved plans need it to speak)."""
    from . import models

    if not models.missing():
        return
    print(f"First run: downloading the local voice model (about 350 MB) into {config.HOME / 'models'} ...")
    try:
        models.download()
    except Exception as exc:  # offline, a proxy...: the app tells the learner how to retry
        print(f"Could not download the voice model ({exc}). Run `dsa-explainer download-models` later.")


def serve(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="dsa-explainer serve")
    parser.add_argument("--host", default=config.HOST)
    parser.add_argument("--port", type=int, default=config.PORT)
    parser.add_argument("--open", action="store_true", help="open the app in the browser")
    parser.add_argument("--no-download", action="store_true", help="do not fetch a missing voice model")
    args = parser.parse_args(argv)
    if not args.no_download:
        ensure_models()

    import uvicorn

    from .api import create_app

    url = f"http://{args.host}:{args.port}"
    if args.open:
        import threading
        import webbrowser

        threading.Timer(1.5, webbrowser.open, [url]).start()
    if not (config.FRONTEND_DIR / "index.html").is_file():
        print(f"Note: the web app is not built ({config.FRONTEND_DIR}); run `npm run build` in frontend/.")
    print(f"DSA Explainer {config.VERSION} on {url}  (data folder: {config.HOME})")
    uvicorn.run(create_app(), host=args.host, port=args.port, log_level="warning")


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        serve(["--open"])
        return
    if argv[0] == "serve":
        serve(argv[1:])
        return
    if argv[0] == "download-models":
        from . import models

        models.download()
        return
    if argv[0] in ("--version", "-V"):
        print(f"dsa-explainer {config.VERSION}")
        return
    from . import pipeline

    parser = argparse.ArgumentParser(prog="dsa-explainer", description="Verified, narrated algorithm lessons.")
    parser.add_argument("topic", nargs="?", help="what to explain")
    parser.add_argument("--level", default="beginner", choices=["beginner", "intermediate", "advanced"])
    parser.add_argument("--quality", default="draft", choices=["draft", "standard", "high"])
    parser.add_argument("--file", help="render a saved lesson plan instead of asking the LLM")
    args = parser.parse_args(argv)
    if args.file:
        result = pipeline.from_file(args.file, args.quality)
    elif args.topic:
        result = pipeline.make_lesson(args.topic, args.level, args.quality)
    else:
        parser.error("give a topic, --file, or the serve command")
    print(f"{result['video']}  ({result['seconds']:.0f} s, {result['clips']} clips, "
          f"{len(result['rendered'])} rendered, {result['reused']} reused)")


if __name__ == "__main__":
    main()
