"""The local model files (Kokoro-82M, about 350 MB), downloaded into the data folder on first run.

Plain HTTPS downloads that resume if interrupted; files already complete are
skipped. Source: https://github.com/thewh1teagle/kokoro-onnx/releases (the
weights are Apache-2.0, from hexgrad/Kokoro-82M). Paths come from config, so a
source checkout uses ./models and an installed copy ~/.dsa-explainer/models.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from . import config

RELEASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"


def files() -> dict[Path, str]:
    return {config.KOKORO_MODEL: f"{RELEASE}/kokoro-v1.0.onnx", config.KOKORO_VOICES: f"{RELEASE}/voices-v1.0.bin"}


def missing() -> list[Path]:
    return [path for path in files() if not path.is_file()]


def download(say: Callable[[str], None] = print) -> None:
    """Fetch every missing model file (resuming partial downloads)."""
    import httpx

    with httpx.Client(timeout=httpx.Timeout(60.0, connect=15.0), follow_redirects=True) as client:
        for dest, url in files().items():
            size = int(client.head(url).headers.get("content-length", 0))
            if dest.is_file() and (not size or dest.stat().st_size == size):
                say(f"ok       {dest}")
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            part = dest.with_suffix(dest.suffix + ".part")
            have = part.stat().st_size if part.exists() else 0
            headers = {"Range": f"bytes={have}-"} if have else {}
            say(f"fetching {url.rsplit('/', 1)[-1]} ({size / 1e6:.0f} MB) into {dest.parent}")
            with client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()
                with part.open("ab" if response.status_code == 206 else "wb") as fh:
                    for block in response.iter_bytes(1 << 20):
                        fh.write(block)
            part.replace(dest)
            say(f"fetched  {dest} ({dest.stat().st_size / 1e6:.0f} MB)")
