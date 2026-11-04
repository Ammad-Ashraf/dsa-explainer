"""Download the local voice model (Kokoro-82M, ~350 MB) into ./models. Run once:

    python scripts/download_models.py

Plain HTTPS downloads that resume if interrupted; files already complete are skipped.
Source: https://github.com/thewh1teagle/kokoro-onnx/releases (Apache 2.0 weights).
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
GH = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
FILES = {
    "models/kokoro/kokoro-v1.0.onnx": f"{GH}/kokoro-v1.0.onnx",
    "models/kokoro/voices-v1.0.bin": f"{GH}/voices-v1.0.bin",
}


def fetch(client: httpx.Client, url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = int(client.head(url, follow_redirects=True).headers.get("content-length", 0))
    if dest.exists() and size and dest.stat().st_size == size:
        print(f"ok       {dest.relative_to(ROOT)}")
        return
    part = dest.with_suffix(dest.suffix + ".part")
    have = part.stat().st_size if part.exists() else 0
    headers = {"Range": f"bytes={have}-"} if have else {}
    with client.stream("GET", url, headers=headers, follow_redirects=True) as response:
        response.raise_for_status()
        with part.open("ab" if response.status_code == 206 else "wb") as fh:
            for block in response.iter_bytes(1 << 20):
                fh.write(block)
    part.replace(dest)
    print(f"fetched  {dest.relative_to(ROOT)} ({dest.stat().st_size / 1e6:.0f} MB)")


def main() -> int:
    with httpx.Client(timeout=httpx.Timeout(60.0, connect=15.0)) as client:
        for rel, url in FILES.items():
            fetch(client, url, ROOT / rel)
    print("voice model ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
