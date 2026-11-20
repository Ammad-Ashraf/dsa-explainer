"""Command line.

    python -m dsa_explainer serve [--port 8000] [--open]       the web app and its API
    python -m dsa_explainer "how does a queue work" --level beginner
    python -m dsa_explainer --file dsa_explainer/plans/stack.json --quality standard
"""

import argparse
import sys

from . import config


def serve(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="dsa_explainer serve")
    parser.add_argument("--host", default=config.HOST)
    parser.add_argument("--port", type=int, default=config.PORT)
    parser.add_argument("--open", action="store_true", help="open the app in the browser")
    args = parser.parse_args(argv)

    import uvicorn

    from .api import create_app

    url = f"http://{args.host}:{args.port}"
    if args.open:
        import threading
        import webbrowser

        threading.Timer(1.5, webbrowser.open, [url]).start()
    print(f"DSA Explainer {config.VERSION} on {url}  (data folder: {config.HOME})")
    uvicorn.run(create_app(), host=args.host, port=args.port, log_level="warning")


def main() -> None:
    if sys.argv[1:2] == ["serve"]:
        serve(sys.argv[2:])
        return
    from . import pipeline

    parser = argparse.ArgumentParser(prog="dsa_explainer")
    parser.add_argument("topic", nargs="?", help="what to explain")
    parser.add_argument("--level", default="beginner", choices=["beginner", "intermediate", "advanced"])
    parser.add_argument("--quality", default="draft", choices=["draft", "standard", "high"])
    parser.add_argument("--file", help="render a saved lesson plan instead of asking the LLM")
    args = parser.parse_args()
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
