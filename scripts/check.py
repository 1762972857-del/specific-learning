#!/usr/bin/env python3
"""Verify one topic: model maths, HTML ↔ Python agreement, page defaults, drafting
palette, offline assets, reader tabs and bundle freshness, ASCII hero, notes.

Run from the topic root (the directory holding viz/ and notes/):

    python viz/check.py            # everything that applies
    python viz/check.py --no-node  # skip the HTML ↔ model.py comparison

model.py supplies evaluate/DEFAULTS/CHECK_CASES (known results) and may define
extra_checks(report) for topic-specific invariants. Static contract checks:
the page's `const DEFAULTS = {...}` literal must agree numerically with
model.DEFAULTS + DEFAULT_INPUTS on shared keys (needs node; WARN if no literal);
every reader tab's data-view (all but "experiment") must be a key of
MARKDOWN_NOTES; page integrity (static HTML ids unique, ids referenced by $('x'),
getElementById, querySelector('#x'), for/aria-*/href="#x" exist unless the scripts create
them at runtime, no tag-like text inside a quoted attribute = lost closing quote; WARN if the
page DEFAULTS literal omits model.DEFAULTS keys); and viz/markdown-bundle.js must match the current notes and
viz/figures files (else run viz/bundle_notes.py). Notes: WARN when the language-neutral
markers <!-- sl:pitfalls|scope|predict --> or one <!-- sl:reading --> per figure are missing. Exit status is 1 if any
ERROR was reported. WARN lines are advisory; SKIP means a check was not performed.
Standard library only.
This is case-based verification, not proof of all mathematical claims.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import math
import re
import shutil
import subprocess
import sys
from html import unescape
from pathlib import Path

ROOT = Path.cwd()
VIZ = ROOT / "viz"
errors = 0
skipped = 0


def report(level: str, msg: str) -> None:
    global errors, skipped
    if level == "ERROR":
        errors += 1
    if level == "SKIP":
        skipped += 1
    print(f"{level:5} {msg}")


def load_model():
    path = VIZ / "model.py"
    if not path.exists():
        report("ERROR", "viz/model.py missing — no model to verify")
        return None
    spec = importlib.util.spec_from_file_location("model", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(VIZ))
    # Read the current source: a fast same-size edit can otherwise reuse stale .pyc.
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
    return mod


def isclose(a: float, b: float, case: dict) -> bool:
    return abs(a - b) <= case["atol"] + case["rtol"] * abs(b)


def resolved_cases(M):
    cases = getattr(M, "CHECK_CASES", None)
    if not isinstance(cases, list) or not cases:
        report("ERROR", "model needs non-empty CHECK_CASES with independent expected values")
        return []
    valid = []
    for index, case in enumerate(cases):
        try:
            expected = case["expected"]
            if not isinstance(expected, dict) or not expected:
                raise ValueError("expected must be a non-empty mapping")
            expected = {key: float(value) for key, value in expected.items()}
            atol, rtol = float(case.get("atol", 1e-9)), float(case.get("rtol", 1e-9))
            if not all(math.isfinite(value) for value in [atol, rtol, *expected.values()]) or min(atol, rtol) < 0:
                raise ValueError("reference values and non-negative tolerances must be finite")
            valid.append({"name": case.get("name", f"case {index}"),
                          "inputs": dict(M.DEFAULT_INPUTS, **case.get("inputs", {})),
                          "params": dict(M.DEFAULTS, **case.get("params", {})),
                          "expected": expected, "atol": atol, "rtol": rtol})
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            report("ERROR", f"CHECK_CASES[{index}]: {exc}")
    return valid


def scalar_outputs(result):
    if not isinstance(result, dict) or not result:
        raise ValueError("evaluate must return a non-empty mapping of named scalar observables")
    values = {key: float(value) for key, value in result.items()}
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError("evaluate returned non-finite output")
    return values


def check_general_model(M, cases):
    for case in cases:
        try:
            actual = scalar_outputs(M.evaluate(case["inputs"], case["params"]))
            for key, reference in case["expected"].items():
                if key not in actual or not isclose(actual[key], reference, case):
                    raise ValueError(f"{key}: actual={actual.get(key)}, expected={reference}")
            report("OK", f"known result: {case['name']}")
        except Exception as exc:
            report("ERROR", f"known result {case['name']}: {exc}")


GENERAL_NODE_HARNESS = r"""
const src = require("fs").readFileSync(0, "utf8");
const cases = JSON.parse(process.argv[1]);
new Function(src)();
const out = cases.map(c => {
  const values = globalThis.MODEL.evaluate(c.inputs, c.params);
  if (!values || Array.isArray(values) || !Object.keys(values).length ||
      !Object.values(values).every(v => typeof v === "number" && Number.isFinite(v))) {
    throw new Error("evaluate must return named finite scalar observables");
  }
  return values;
});
console.log(JSON.stringify(out));
"""


def check_general_html(html, name, M, cases):
    block = re.search(r'<script\b[^>]*\bid=["\']lab-model["\'][^>]*>(.*?)</script>', html, re.S)
    if not block or not cases:
        return  # Missing block/cases is already an error, not a silent pass.
    if not shutil.which("node"):
        report("SKIP", "node not found — HTML ↔ model.py comparison not performed")
        return
    run = subprocess.run(["node", "-e", GENERAL_NODE_HARNESS, json.dumps(cases)],
                         input=block.group(1), capture_output=True, text=True)
    if run.returncode:
        report("ERROR", f"{name}: lab-model failed: {run.stderr.strip()}")
        return
    try:
        rows = json.loads(run.stdout)
        if len(rows) != len(cases):
            raise ValueError("wrong result count")
        for case, js in zip(cases, rows):
            py = scalar_outputs(M.evaluate(case["inputs"], case["params"]))
            if py.keys() != js.keys():
                raise ValueError(f"{case['name']}: Python/JS output names differ")
            for key in py:
                if not isclose(py[key], js[key], case):
                    raise ValueError(f"{case['name']}: {key} differs between Python and JS")
        report("OK", f"{name}: Python/JS agree on all observables in {len(cases)} cases")
    except (ValueError, TypeError, KeyError) as exc:
        report("ERROR", f"{name}: {exc}")


# ---------------------------------------------------------------- HTML
# Drafting palette (assets/draft.css :root). Pages and figures.py use these values only;
# pages should reference var(--…) rather than literals.
ALLOWED_HEX = {
    "#eceae3", "#e3e0d6",  # paper
    "#1b1b19",             # ink (alpha variants: rgb(27 27 25 / N%))
    "#d4572a", "#b4441c",  # vermilion: current selection / its text
    "#8fa8bf",             # fog blue: region
}
ALLOWED_RGB = {(27, 27, 25), (212, 87, 42), (143, 168, 191)}
HEX = re.compile(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b")
RGB = re.compile(r"rgba?\(\s*(\d+)[ ,]+(\d+)[ ,]+(\d+)")


def colour_literals(text: str, ids: set[str]) -> list[str]:
    bad = [h for h in HEX.findall(text) if h.lower() not in ALLOWED_HEX and h[1:] not in ids]
    bad += [m.group(0) for m in RGB.finditer(text) if tuple(int(v) for v in m.groups()) not in ALLOWED_RGB]
    return bad


def local_refs(html: str) -> list[str]:
    refs = re.findall(r'<script\b[^>]*\bsrc=["\']([^"\']+)["\']', html)
    refs += re.findall(r'<link\b[^>]*\bhref=["\']([^"\']+)["\'][^>]*>', html)
    return refs


def check_palette(html: str, name: str, page: Path) -> None:
    ids = set(re.findall(r'\bid=["\']([\w-]+)["\']', html))
    sources = [(name, html)]
    for href in local_refs(html):
        if href.endswith(".css") and not re.match(r"[a-z]+:|//", href):
            sheet = (page.parent / href).resolve()
            if sheet.exists():
                sources.append((sheet.name, sheet.read_text(encoding="utf-8")))
    figures = VIZ / "figures.py"
    if figures.exists():
        sources.append(("viz/figures.py", figures.read_text(encoding="utf-8")))
    bad = [f"{label}:{lit}" for label, text in sources for lit in colour_literals(text, ids)]
    if bad:
        report("ERROR", f"{name}: colours outside the drafting palette (recipe.md §2): {', '.join(sorted(set(bad)))}")
    else:
        report("OK", f"{name}: palette within draft.css tokens ({len(sources) - 1} linked file(s) scanned)")


def check_assets(html: str, name: str, page: Path) -> None:
    """Offline-first: no CDN scripts or stylesheets, every local asset present."""
    external = [r for r in local_refs(html) if re.match(r"(https?:)?//", r)]
    external += re.findall(r"@import\s+url\(\s*['\"]?((?:https?:)?//[^)'\"]+)", html)
    if external:
        report("ERROR", f"{name}: external script/stylesheet {', '.join(external)}; vendor it under viz/assets/vendor")
    missing = [r for r in local_refs(html) if not re.match(r"[a-z]+:|//|#", r) and not (page.parent / r.split("?")[0]).exists()]
    for r in missing:
        hint = " (run python viz/bundle_notes.py)" if r.endswith("markdown-bundle.js") else ""
        report("ERROR", f"{name}: local asset {r} not found{hint}")
    if not external and not missing:
        report("OK", f"{name}: all scripts and stylesheets are local")


def check_hero(html: str, name: str) -> None:
    section = re.search(r'<section\b[^>]*class=["\'][^"\']*\bhero\b[^"\']*["\'][^>]*>(.*?)</section>', html, re.S)
    figure = section and re.search(r'<figure\b([^>]*class=["\'][^"\']*\bhero-ascii\b[^"\']*["\'][^>]*)>(.*?)</figure>', section.group(1), re.S)
    if not figure:
        report("ERROR", f"{name}: hero needs figure.hero-ascii")
        return
    bad = []
    attrs, content = figure.groups()
    if not re.search(r'\brole=["\']img["\']', attrs) or not re.search(r'\baria-label=["\'][^"\']+', attrs):
        bad.append("figure needs role=img and a nonempty aria-label")
    pre = re.search(r'<pre\b[^>]*>(.*?)</pre>', content, re.S)
    if not pre:
        bad.append("missing pre")
    else:
        art = re.sub(r'</?span\b[^>]*>', '', pre.group(1))
        if re.search(r'<[^>]+>', art):
            bad.append("pre allows text and span elements only")
        lines = unescape(art).strip('\n').splitlines()
        if not any(line.strip() for line in lines):
            bad.append("empty ASCII art")
        if any(ord(ch) < 32 or ord(ch) > 126 for line in lines for ch in line):
            bad.append("use printable ASCII and spaces, without tabs or escape sequences")
        if len(lines) > 32 or any(len(line) > 64 for line in lines):
            report("WARN", f"{name}: ASCII exceeds suggested 64 columns / 32 lines; verify narrow layout")
    if not re.search(r'<figcaption\b[^>]*>\s*\S', content):
        bad.append("missing explanatory figcaption")
    report("ERROR" if bad else "OK", f"{name}: ASCII hero " + ('; '.join(bad) if bad else 'has content, description and caption'))


def check_structure(html: str, name: str) -> None:
    # Teaching modules and the workspace layout are topic choices.
    if not re.search(r'<script\b[^>]*\bid=["\']lab-model["\']', html):
        report("ERROR", f"{name}: missing pure lab-model block")
    left = sorted(set(re.findall(r"\{\{[^}]+\}\}", html)))
    if left:
        report("ERROR", f"{name}: unfilled placeholders {', '.join(left)}")



# ---------------------------------------------------------------- page contracts
def js_object_literal(html: str, name: str = "DEFAULTS") -> str | None:
    """Source of the first `const NAME = {...}` literal, by balanced-brace scan."""
    m = re.search(rf"\b(?:const|let|var)\s+{name}\s*=\s*\{{", html)
    if not m:
        return None
    start, depth, i, quote = m.end() - 1, 0, m.end() - 1, None
    while i < len(html):
        ch = html[i]
        if quote:
            i += 2 if ch == "\\" else 1
            quote = None if ch == quote else quote
            continue
        if html.startswith("/*", i) or html.startswith("//", i):
            end = html.find("*/" if html[i + 1] == "*" else "\n", i + 2)
            if end < 0:
                return None
            i = end + (2 if html[i + 1] == "*" else 1)
            continue
        if ch in "'\"`":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return html[start:i + 1]
        i += 1
    return None


def is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check_defaults(html: str, name: str, M) -> None:
    """Page DEFAULTS must match model DEFAULTS + DEFAULT_INPUTS on every shared key."""
    literal = js_object_literal(html)
    if literal is None:
        report("WARN", f"{name}: no `const DEFAULTS = {{...}}` literal found; defaults agreement not checked")
        return
    if not shutil.which("node"):
        report("SKIP", "node not found — page DEFAULTS vs model.py comparison not performed")
        return
    run = subprocess.run(["node", "-e", 'process.stdout.write(JSON.stringify(new Function("return (" + process.argv[1] + ")")()))', literal],
                         capture_output=True, text=True)
    try:
        if run.returncode:
            raise ValueError(run.stderr.strip().splitlines()[-1] if run.stderr.strip() else "node failed")
        page = json.loads(run.stdout)
        if not isinstance(page, dict):
            raise ValueError("not an object")
    except (ValueError, json.JSONDecodeError) as exc:
        report("WARN", f"{name}: DEFAULTS literal not evaluable ({exc}); defaults agreement not checked")
        return
    model = dict(getattr(M, "DEFAULTS", {}), **getattr(M, "DEFAULT_INPUTS", {}))
    shared = sorted(page.keys() & model.keys())
    if not shared:
        report("WARN", f"{name}: page DEFAULTS and model DEFAULTS/DEFAULT_INPUTS share no keys; defaults agreement not checked")
        return
    lost = sorted(set(getattr(M, "DEFAULTS", {})) - page.keys())
    if lost:
        report("WARN", f"{name}: page DEFAULTS lacks model DEFAULTS keys {', '.join(lost)}; add them or confirm the page keeps them elsewhere")
    bad = [f"{k}: page={page[k]} model={model[k]}" for k in shared
           if is_number(page[k]) and is_number(model[k]) and abs(page[k] - model[k]) > 1e-12 + 1e-12 * abs(model[k])]
    if bad:
        report("ERROR", f"{name}: page DEFAULTS disagree with model.py ({'; '.join(bad)}); make both initial states equal")
    else:
        report("OK", f"{name}: DEFAULTS agree with model.py on {len(shared)} shared keys")


def static_markup(html: str) -> str:
    """HTML with comments, script and style bodies blanked (newlines kept for line numbers)."""
    blank = lambda m: re.sub(r"[^\n]", " ", m.group(0))
    return re.sub(r"<!--.*?-->|<(script|style)\b.*?</\1>", blank, html, flags=re.S | re.I)


def check_integrity(html: str, name: str, page: Path) -> None:
    """Static ids unique, referenced ids exist, no lost attribute quotes."""
    markup = static_markup(html)
    line = lambda pos: markup.count("\n", 0, pos) + 1
    bad = []
    for m in re.finditer(r"<[A-Za-z][\w-]*", markup):  # quote-aware tag walk
        i, quote = m.end(), None
        while i < len(markup) and (quote or markup[i] != ">"):
            if quote and re.match(r"<[A-Za-z/!][\w-]*[\s>/]", markup[i:i + 40]):
                bad.append(f"line {line(m.start())} <{m.group(0)[1:]}: tag-like text in quoted attribute")
                break
            quote = None if markup[i] == quote else quote or (markup[i] if markup[i] in "\"'" and markup[i - 1] == "=" else None)
            i += 1
        else:
            if quote:
                bad.append(f"line {line(m.start())} <{m.group(0)[1:]}: unclosed quote")
    if bad:
        report("ERROR", f"{name}: malformed attribute ({'; '.join(bad[:5])}); restore the missing closing quote")
    ids = re.findall(r'\bid=["\']([^"\']+)["\']', markup)
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        report("ERROR", f"{name}: duplicate id {', '.join(dup)}; ids must be unique")
    scripts = [b for b in re.findall(r"<script\b(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S | re.I)]
    for src in local_refs(html):  # linked local scripts (draft.js) may create ids too
        path = (page.parent / src.split("?")[0]).resolve()
        if src.endswith(".js") and not re.match(r"[a-z]+:|//", src) and path.is_file() and "vendor" not in path.parts:
            scripts.append(path.read_text(encoding="utf-8", errors="replace"))
    js = "\n".join(scripts)
    made = set(re.findall(r'\bid=\\?["\']([\w-]+)\\?["\']', js)) | set(re.findall(r'\.id\s*=\s*["\']([\w-]+)["\']', js))
    prefixes = re.findall(r'(?:\bid=\\?["\']|\.id\s*=\s*[`"\'])([\w-]*)\$\{', js)
    refs = set(re.findall(r"\$\(\s*(['\"])([\w-]+)\1\s*\)", js)) | set(re.findall(r"getElementById\(\s*(['\"])([\w-]+)\1\s*\)", js)) \
        | set(re.findall(r"querySelector\(\s*(['\"])#([\w-]+)[^'\"]*\1", js))
    names = {n for _, n in refs}
    for attr in re.findall(r'\b(?:aria-describedby|aria-labelledby|aria-controls|for)=["\']([^"\']+)["\']', markup):
        names |= set(attr.split())
    names |= set(re.findall(r'<a\b(?![^>]*\bdata-view=)[^>]*\bhref=["\']#([\w-]+)["\']', markup))
    gone = sorted(n for n in names if n not in ids and n not in made and not any(n.startswith(p) for p in prefixes if p))
    if gone:
        report("ERROR", f"{name}: referenced id not in HTML: {', '.join(gone)}; fix the id or the reference")
    elif not bad and not dup:
        report("OK", f"{name}: {len(ids)} ids unique, {len(names)} referenced ids exist, attributes well-formed")


def load_bundle():
    """(notes, figures) from viz/markdown-bundle.js; None if absent or unreadable (reported)."""
    path = VIZ / "markdown-bundle.js"
    if not path.exists():
        return None  # check_assets reports it when the page references the bundle.
    text = path.read_text(encoding="utf-8")
    try:
        dec, parts, pos = json.JSONDecoder(), [], 0
        for var in ("MARKDOWN_NOTES", "FIGURE_DATA"):
            m = re.compile(rf"\s*(?:;\s*)?window\.{var}\s*=\s*").match(text, pos)
            obj, pos = dec.raw_decode(text, m.end())
            parts.append(obj)
        if not all(isinstance(p, dict) for p in parts):
            raise ValueError("payloads must be objects")
        return parts[0], parts[1]
    except (AttributeError, ValueError) as exc:
        report("ERROR", f"viz/markdown-bundle.js unreadable ({exc}); run viz/bundle_notes.py")
        return None


def figure_payload() -> dict:
    """Current viz/figures as bundle_notes.py would encode them."""
    out = {}
    for fig in sorted((VIZ / "figures").iterdir()) if (VIZ / "figures").is_dir() else ():
        mime = {".png": "image/png", ".svg": "image/svg+xml"}.get(fig.suffix.lower())
        if fig.is_file() and mime:
            out[fig.name] = f"data:{mime};base64," + base64.b64encode(fig.read_bytes()).decode("ascii")
    return out


def check_bundle_fresh(bundle) -> None:
    if bundle is None:
        return
    notes, figures = bundle
    diff = []
    for key, entry in notes.items():
        try:
            current = (ROOT / entry["file"]).read_text(encoding="utf-8")
        except (OSError, KeyError, TypeError, UnicodeDecodeError):
            diff.append(f"note {key} unreadable or file missing")
            continue
        if entry.get("source") != current:
            diff.append(f"note {entry['file']} changed")
    now = figure_payload()
    for label, names in (("changed", [n for n in figures.keys() & now.keys() if figures[n] != now[n]]),
                         ("added", list(now.keys() - figures.keys())), ("removed", list(figures.keys() - now.keys()))):
        diff += [f"figure {n} {label}" for n in sorted(names)]
    if diff:
        report("ERROR", f"stale viz/markdown-bundle.js: {'; '.join(diff)}; run viz/bundle_notes.py")
    else:
        report("OK", f"viz/markdown-bundle.js matches {len(notes)} note(s) and {len(figures)} figure(s)")


def check_tabs(html: str, name: str, bundle) -> None:
    """Reader tabs open MARKDOWN_NOTES[data-view]; "experiment" only scrolls (draft.js shell)."""
    if bundle is None:
        return
    views = sorted(set(re.findall(r'<a\b[^>]*\bdata-view=["\']([^"\']+)["\']', html)) - {"experiment"})
    missing = [v for v in views if v not in bundle[0]]
    if missing:
        report("ERROR", f"{name}: reader tab data-view {', '.join(missing)} not in viz/markdown-bundle.js "
                        f"(keys: {', '.join(bundle[0]) or 'none'}); fix the tab or bundle with that key")
    else:
        report("OK", f"{name}: {len(views)} reader tab(s) match bundle keys")


# ---------------------------------------------------------------- notes
SRC_TAG = re.compile(r"\[(?:Source|Derivation|Inference|Standard result)\]", re.I)
# Language-neutral markers (figures.md#note-markers): `<!-- sl:NAME -->` after the section heading / before each reading block.
SECTIONS = {"pitfalls": "pitfalls", "scope": "units and scope", "predict": "prediction"}


def check_notes() -> None:
    notes = sorted((ROOT / "notes").glob("*.md"))
    if not notes:
        report("ERROR", "notes/*.md not found")
        return
    for md in notes:
        text = md.read_text(encoding="utf-8")
        rel = md.relative_to(ROOT)
        for target in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text):
            if not target.startswith("http") and not (md.parent / target).resolve().exists():
                report("ERROR", f"{rel}: missing figure {target}")
        left = sorted(set(re.findall(r"\{\{[^}]+\}\}", text)))
        if left:
            report("ERROR", f"{rel}: {len(left)} unfilled placeholders, e.g. {left[0]}")
        tags = len(SRC_TAG.findall(text))
        report("OK" if tags else "WARN", f"{rel}: {tags} provenance tags")
        for key, label in SECTIONS.items():
            if not re.search(rf"<!--\s*sl:{key}\s*-->", text):
                report("WARN", f"{rel}: no <!-- sl:{key} --> marker for the {label} section")
        n_fig = len(re.findall(r"!\[", text))
        n_read = len(re.findall(r"<!--\s*sl:reading\s*-->", text))
        if n_fig and n_read < n_fig:
            report("WARN", f"{rel}: {n_fig} figures but {n_read} <!-- sl:reading --> markers")


def check_template_origin() -> None:
    """Flag files still byte-identical to the scaffold template (viz/.template-origin)."""
    origin = VIZ / ".template-origin"
    if not origin.exists():
        return
    try:
        recorded = json.loads(origin.read_text(encoding="utf-8"))["files"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        report("WARN", f"viz/.template-origin unreadable: {exc}")
        return
    for rel, digest in sorted(recorded.items()):
        path = ROOT / rel
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == digest:
            report("WARN", f"unadapted template file: {rel}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-node", action="store_true")
    args = ap.parse_args()

    try:
        M = load_model()
        cases = []
        if M is not None:
            if not hasattr(M, "evaluate"):
                report("ERROR", "model.py must define evaluate(inputs, params) -> dict of scalar observables")
                M = None
            else:
                cases = resolved_cases(M)
                check_general_model(M, cases)
                if hasattr(M, "extra_checks"):
                    M.extra_checks(report)
    except Exception as exc:
        report("ERROR", f"model checks failed: {exc}")
        M = None
    pages = sorted(VIZ.glob("*.html"))
    if not pages:
        report("ERROR", "viz/*.html not found")
    if args.no_node:
        report("SKIP", "--no-node: Python/JS comparison explicitly disabled")
    bundle = load_bundle()
    check_bundle_fresh(bundle)
    for page in pages:
        html = page.read_text(encoding="utf-8")
        name = str(page.relative_to(ROOT))
        check_palette(html, name, page)
        check_assets(html, name, page)
        check_hero(html, name)
        check_structure(html, name)
        check_tabs(html, name, bundle)
        check_integrity(html, name, page)
        if M and not args.no_node:
            check_general_html(html, name, M, cases)
            check_defaults(html, name, M)
    check_notes()
    check_template_origin()
    print(f"\n{errors} error(s), {skipped} skipped check(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
