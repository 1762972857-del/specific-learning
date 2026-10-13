#!/usr/bin/env python3
"""Scaffold a standalone topic from a layout/drawing template. Never overwrite files."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = SKILL / "templates"
# Registered from the directory listing: a new templates/<name>/ appears automatically.
TEMPLATES = tuple(sorted(p.name for p in TEMPLATES_DIR.iterdir() if (p / "viz" / f"{p.name}.html").is_file())) \
    if TEMPLATES_DIR.is_dir() else ()
SKIP_NAMES = {"__pycache__", ".DS_Store", ".venv"}


def copy_missing(src: Path, dst: Path) -> list[Path]:
    """Copy src into dst without overwriting; return the files actually written."""
    written: list[Path] = []
    if src.is_dir():
        for child in sorted(src.iterdir()):
            if child.name not in SKIP_NAMES and child.suffix != ".pyc":
                written += copy_missing(child, dst / child.name)
    elif not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        written.append(dst)
    return written


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dest", type=Path)
    ap.add_argument("slug", help="HTML file stem, without a path or extension")
    ap.add_argument("--template", choices=TEMPLATES, default=TEMPLATES[0] if TEMPLATES else None)
    ap.add_argument("--source", choices=("prompt", "courseware"), default="prompt")
    ap.add_argument("--lang", default="en", help="BCP 47 language tag for <html lang> (default en)")
    ap.add_argument("--main", help="optional page title; does not change the template's model")
    ap.add_argument("--sub", help="optional subtitle")
    a = ap.parse_args()
    if not a.template:
        ap.error(f"no templates found under {TEMPLATES_DIR}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", a.slug):
        ap.error("slug must contain only letters, digits, underscores and hyphens")
    if not re.fullmatch(r"[A-Za-z]{2,3}(-[A-Za-z0-9]{1,8})*", a.lang):
        ap.error("--lang must be a BCP 47 tag such as en, zh-CN, zh-Hant or ja")
    dest = a.dest.expanduser().resolve()
    template = TEMPLATES_DIR / a.template
    protected = (SKILL / "assets", TEMPLATES_DIR, SKILL / "examples")
    if dest == SKILL or any(dest == p or p in dest.parents for p in protected):
        ap.error("choose an output directory outside the skill's templates, examples and shared assets")
    source_page = template / "viz" / f"{a.template}.html"

    written: list[Path] = []
    for path in sorted(template.rglob("*")):
        rel = path.relative_to(template)
        if path.is_dir() or SKIP_NAMES & set(rel.parts) or path.suffix == ".pyc" or path == source_page:
            continue
        new = copy_missing(path, dest / rel)
        for target in new:
            if target.suffix == ".md":
                target.write_text(target.read_text(encoding="utf-8").replace(
                    f"{a.template}.html", f"{a.slug}.html"), encoding="utf-8")
        written += new
    page = dest / "viz" / f"{a.slug}.html"
    if not page.exists():
        text = source_page.read_text(encoding="utf-8")
        text = re.sub(r'<html lang="[^"]*"', lambda _: f'<html lang="{a.lang}"', text, count=1)
        if a.main:
            title = html.escape(a.main, quote=True)
            latin = ' class="latin"' if a.main.isascii() else ""
            text = re.sub(r"<title>.*?</title>", lambda _: f"<title>{title}</title>", text, count=1)
            text = re.sub(r"<h1\b[^>]*>.*?</h1>", lambda _: f'<h1{latin}>{title}</h1>', text, count=1, flags=re.S)
        if a.sub:
            text = re.sub(r'<p class="sub">.*?</p>', lambda _: f'<p class="sub">{html.escape(a.sub)}</p>', text, count=1, flags=re.S)
        page.write_text(text, encoding="utf-8")
        written.append(page)
    viz = dest / "viz"
    for script in ("check.py", "bundle_notes.py", "build.py", "qa.py"):
        written += copy_missing(SKILL / "scripts" / script, viz / script)
    copy_missing(SKILL / "assets", viz / "assets")
    if a.source == "courseware":
        (dest / "sources").mkdir(parents=True, exist_ok=True)
    origin = viz / ".template-origin"
    if not origin.exists():
        tracked = [p for p in written if p == viz / "model.py" or p == page or p.parent == dest / "notes"]
        origin.write_text(json.dumps(
            {"template": a.template, "files": {str(p.relative_to(dest)): sha256(p) for p in tracked}},
            indent=2) + "\n", encoding="utf-8")
    # Bundle the copied notes after their HTML filename references have changed.
    if not (viz / "markdown-bundle.js").exists():
        subprocess.run([sys.executable, str(SKILL / "scripts" / "bundle_notes.py")], cwd=dest, check=True)
    ignore = dest / ".gitignore"
    if not ignore.exists():
        ignore.write_text(".DS_Store\n__pycache__/\n*.pyc\n.venv/\n"
                          "sources/raw.md\nsources/*.pdf\nsources/*.pptx\nsources/*.docx\n", encoding="utf-8")
    print(f"Ready: {page}\nTemplate: {a.template}; source: {a.source}")
    print("The template supplies layout and drawing code only. Replace every TOPIC: placeholder and adapt the model, views, figures and notes together.")
    print("For natural-language topics, verify authoritative lecture/technical sources online first.")
    print("From the topic root run python3 viz/build.py after editing (figures, bundle, checks); check.py WARNs on files still identical to the template.")


if __name__ == "__main__":
    main()
