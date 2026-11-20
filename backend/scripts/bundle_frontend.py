"""Copy the built web app (frontend/dist) into the Python package (dsa_explainer/web) before building a wheel.

    cd frontend && npm ci && npm run build && cd ..
    python backend/scripts/bundle_frontend.py
    python -m build

An installed `dsa-explainer` serves the app from dsa_explainer/web (config.FRONTEND_DIR); a source checkout
serves frontend/dist directly, so this step is only for packaging. dsa_explainer/web is not in git.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "frontend" / "dist"
WEB = ROOT / "backend" / "dsa_explainer" / "web"


def main() -> int:
    if not (DIST / "index.html").is_file():
        print(f"no built web app in {DIST}: run `npm ci && npm run build` in frontend/ first", file=sys.stderr)
        return 1
    shutil.rmtree(WEB, ignore_errors=True)
    shutil.copytree(DIST, WEB)
    files = sum(1 for p in WEB.rglob("*") if p.is_file())
    print(f"bundled {files} files into {WEB.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
