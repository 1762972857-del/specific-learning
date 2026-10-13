#!/usr/bin/env python3
"""Build one topic: figures (if viz/figures.py), notes bundle, then checks.

Run from the topic root (the directory holding viz/ and notes/):

    python3 viz/build.py [--no-figures] [--no-node] [--qa] [key=Title=path ...]

Steps: viz/figures.py (skipped by --no-figures or when absent), viz/bundle_notes.py
(note arguments are forwarded), viz/check.py (--no-node is forwarded), then with --qa
viz/qa.py after a passing check (exit 2 there means the browser run was not possible). Stops at the
first failing step; exits with check.py's status. Each step runs with this Python.
If figures.py or check.py reports a missing module and uv is on PATH, the step is
retried once through `uv run --no-project` with requirements.txt (or the missing
module). Without uv the exact command is printed with the uv install URL. Launched
through `uv run --no-project python viz/build.py`, steps reuse that interpreter. Never installs into this Python.
Standard library only.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
MISSING = re.compile(r"No module named '([^'.]+)")


def die(msg: str, code: int = 1) -> None:
    print(f"build: {msg}", file=sys.stderr)
    sys.exit(code)


def run(label: str, script: str, args: list[str], uv_retry: bool = False) -> int:
    """Run viz/<script>; stdout+stderr are captured so a missing module can be detected."""
    def go(cmd):
        return subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, errors="replace")
    how, p = f"python {sys.executable}", go([sys.executable, script, *args])
    miss = MISSING.search(p.stdout) if uv_retry and p.returncode else None
    if miss:
        spec = ["--with-requirements", "requirements.txt"] if (ROOT / "requirements.txt").is_file() \
            else ["--with", miss[1]]
        cmd = ["uv", "run", "--no-project", *spec, "python", script, *args]
        if not shutil.which("uv"):
            print(f"== {label}: {script} [{how}]\n{p.stdout}", end="")
            die(f"missing Python module '{miss[1]}' and uv is not installed. Install uv "
                f"(https://docs.astral.sh/uv/getting-started/installation/) and run:\n  {' '.join(cmd)}\n"
                "or use a project virtual environment that provides the module.")
        how, p = "uv " + " ".join(spec), go(cmd)
    print(f"== {label}: {script} [{how}]\n{p.stdout}", end="")
    return p.returncode


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-figures", action="store_true", help="skip viz/figures.py")
    ap.add_argument("--no-node", action="store_true", help="pass --no-node to check.py")
    ap.add_argument("--qa", action="store_true", help="run viz/qa.py (browser acceptance) after a passing check")
    ap.add_argument("notes", nargs="*", metavar="key=Title=path", help="forwarded to bundle_notes.py")
    a = ap.parse_args()
    if not (ROOT / "viz").is_dir():
        die("no viz/ here; run from the topic root")
    if a.no_figures or not (ROOT / "viz" / "figures.py").is_file():
        print("== figures: skipped" + (" (--no-figures)" if a.no_figures else " (no viz/figures.py)"))
    elif run("figures", "viz/figures.py", [], True):
        die("viz/figures.py failed; stopping")
    if run("bundle", "viz/bundle_notes.py", a.notes):
        die("viz/bundle_notes.py failed; stopping")
    rc = run("check", "viz/check.py", ["--no-node"] * a.no_node, True)
    if a.qa and rc == 0:
        if not (ROOT / "viz" / "qa.py").is_file():
            die("--qa needs viz/qa.py (copy it from the skill's scripts/)")
        rc = run("qa", "viz/qa.py", [])
    sys.exit(rc)


if __name__ == "__main__":
    main()
