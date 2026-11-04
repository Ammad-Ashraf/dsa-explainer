"""Command line, for testing without the web page:

    python -m dsa_explainer "how does a queue work" --level beginner
    python -m dsa_explainer --file examples/stack.json --quality standard
"""

import argparse

from . import pipeline


def main() -> None:
    parser = argparse.ArgumentParser(prog="dsa_explainer")
    parser.add_argument("topic", nargs="?", help="what to explain")
    parser.add_argument("--level", default="beginner", choices=["beginner", "intermediate", "advanced"])
    parser.add_argument("--quality", default="draft", choices=["draft", "standard"])
    parser.add_argument("--file", help="render a saved lesson plan instead of asking the LLM")
    args = parser.parse_args()
    if args.file:
        result = pipeline.from_file(args.file, args.quality)
    elif args.topic:
        result = pipeline.make_lesson(args.topic, args.level, args.quality)
    else:
        parser.error("give a topic or --file")
    print(f"{result['video']}  ({result['seconds']:.0f} s, {result['clips']} clips, "
          f"{len(result['rendered'])} rendered, {result['reused']} reused)")


if __name__ == "__main__":
    main()
