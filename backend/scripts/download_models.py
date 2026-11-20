"""Download the local voice model (Kokoro-82M, ~350 MB) into the data folder. Run once:

    python backend/scripts/download_models.py

The installed command does this by itself on first run (`dsa-explainer`); see dsa_explainer/models.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dsa_explainer import models  # noqa: E402


def main() -> int:
    models.download()
    print("voice model ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
