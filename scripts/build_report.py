"""Builds docs/report.pdf from docs/report.md, using Microsoft Edge or Google Chrome to print it.

    python scripts/build_report.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

DOCS = Path(__file__).resolve().parents[1] / "docs"
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "chromium", "microsoft-edge",
]
CSS = """
@page { size: A4; margin: 17mm 16mm; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #1f2933; }
h1 { font-size: 24pt; margin: 0 0 6pt; color: #0f172a; }
h2 { font-size: 15pt; margin: 20pt 0 6pt; padding-bottom: 3pt; border-bottom: 1px solid #cbd5e1; color: #0f172a;
     page-break-after: avoid; }
h3 { font-size: 12pt; margin: 14pt 0 4pt; color: #0f172a; page-break-after: avoid; }
p, li { orphans: 3; widows: 3; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 9.5pt; page-break-inside: avoid; }
th, td { border: 1px solid #cbd5e1; padding: 4pt 6pt; text-align: left; vertical-align: top; }
th { background: #f1f5f9; }
th:empty { display: none; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9pt; background: #f1f5f9; padding: 0 2pt;
       border-radius: 3px; }
pre { background: #f1f5f9; padding: 8pt 10pt; border-radius: 4px; white-space: pre-wrap; font-size: 8.5pt;
      page-break-inside: avoid; }
pre code { background: none; padding: 0; }
img { max-width: 100%; border-radius: 6px; }
hr { border: none; border-top: 1px solid #cbd5e1; margin: 12pt 0; }
"""


def find_browser() -> str:
    for name in BROWSERS:
        if Path(name).exists():
            return name
        if shutil.which(name):
            return shutil.which(name)
    sys.exit("Microsoft Edge or Google Chrome is needed to print the PDF.")


def main() -> None:
    body = markdown.markdown((DOCS / "report.md").read_text(encoding="utf-8"), extensions=["tables", "fenced_code"])
    page = DOCS / "_report.html"  # next to the images it refers to
    page.write_text(f"<!doctype html><html><head><meta charset='utf-8'><title>DSA Explainer report</title>"
                    f"<style>{CSS}</style></head><body>{body}</body></html>", encoding="utf-8")
    out = DOCS / "report.pdf"
    try:
        with tempfile.TemporaryDirectory() as profile:
            subprocess.run([find_browser(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                            f"--user-data-dir={profile}", f"--print-to-pdf={out}", page.as_uri()],
                           check=True, capture_output=True, timeout=180)
    finally:
        page.unlink(missing_ok=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
