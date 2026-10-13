#!/usr/bin/env python3
"""Pack the Markdown notes and figures into viz/markdown-bundle.js.

The HTML reader prefers live fetch when served over http, and falls back
to this bundle so double-clicking the page still works.

Run from the topic root. Each note is key=title=path; the key must match a
tab's data-view in the HTML:

    python viz/bundle_notes.py guide=Guide=notes/01-topic.md annotated=Source=sources/annotated.md

With no arguments it bundles notes/*.md as guide (first file) and
sources/annotated.md as annotated, if present.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
VIZ = ROOT / "viz"
OUT = VIZ / "markdown-bundle.js"
FIGURES = VIZ / "figures"


def default_notes() -> list[tuple[str, str, Path]]:
    found = []
    guides = sorted((ROOT / "notes").glob("*.md"))
    if guides:
        found.append(("guide", "Guide", guides[0]))
    annotated = ROOT / "sources" / "annotated.md"
    if annotated.exists():
        found.append(("annotated", "Source", annotated))
    return found


def parse(argv: list[str]) -> list[tuple[str, str, Path]]:
    notes = []
    for arg in argv:
        key, title, path = arg.split("=", 2)
        notes.append((key, title, ROOT / path))
    return notes


def main() -> None:
    notes = parse(sys.argv[1:]) or default_notes()
    if not notes:
        sys.exit("no notes found; pass key=title=path")
    payload = {}
    for key, title, path in notes:
        payload[key] = {
            "title": title,
            "file": str(path.relative_to(ROOT)),
            # Relative to viz/, where the HTML lives.
            "url": "../" + str(path.relative_to(ROOT)),
            "source": path.read_text(encoding="utf-8"),
        }
    figures = {}
    for figure in sorted(FIGURES.iterdir()) if FIGURES.exists() else ():
        mime = {".png": "image/png", ".svg": "image/svg+xml"}.get(figure.suffix.lower())
        if figure.is_file() and mime:
            figures[figure.name] = f"data:{mime};base64," + base64.b64encode(figure.read_bytes()).decode("ascii")
    OUT.write_text(
        "window.MARKDOWN_NOTES = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\nwindow.FIGURE_DATA = "
        + json.dumps(figures, ensure_ascii=False)
        + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT} ({len(payload)} notes, {len(figures)} figures)")


if __name__ == "__main__":
    main()
