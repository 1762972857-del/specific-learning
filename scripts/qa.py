#!/usr/bin/env python3
"""Browser acceptance for one topic: HTTP and file://, desktop and phone widths.

Run from the topic root (the directory holding viz/ and notes/):

    python3 viz/qa.py [--out DIR] [--widths 1440,390] [--no-file]

Per page and width it records console errors, page errors, failed requests, KaTeX
errors, raw math ($..$, \\frac, **) in visible text and in each opened reader tab,
horizontal overflow, zero-size or blank canvases, reader open/Escape-close for every
data-view tab, and (reduced motion) that #play is not pressed on load. Screenshots go
to --out (default ../<topic>-qa/) as <topic>-<scenario>-<width>.png, with qa-report.json.

Optional viz/qa.json declares topic interactions: a list of steps run over HTTP at every
width, each on a fresh page load (defaults), then swept and screenshotted:
  {"name": "...", "do": [ACTION...], "expect": [EXPECT...]}
  ACTION: {"fill": SEL, "value": V} {"select": SEL, "value": V} {"click": SEL}
          {"press": KEY, "on": SEL (optional)} {"drag": SEL, "from": [fx,fy], "to": [fx,fy]}
  EXPECT: {"changed": SEL} (text, value or canvas pixels differ from before the step)
          {"text": SEL, "matches": REGEX}
Fractions are relative to the element box.

Needs playwright: if not importable, re-runs itself once through
`uv run --no-project --with playwright`. Uses an existing Playwright Chromium from the
browser cache when the default one is missing; never downloads a browser.
Exit 0 passed, 1 checks failed, 2 could not run. Standard library and playwright only.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path.cwd()
CACHES = ("~/Library/Caches/ms-playwright", "~/.cache/ms-playwright")
VERBS = {"fill": ("value",), "select": ("value",), "click": (), "press": ("on",), "drag": ("from", "to")}

SWEEP = r"""() => {
  const vis = e => e.checkVisibility({visibilityProperty: true}), out = {raw: [], canvas: []};
  const re = /\$\S[^$\n]*\$|\\frac|\\[a-zA-Z]{2,}\{|\*\*/, w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = w.nextNode());) {
    const p = n.parentElement, m = p && n.nodeValue.match(re);
    if (m && !p.closest('script,style,pre,code,textarea,.katex-mathml') && vis(p)) out.raw.push(m[0] + ' in <' + p.tagName.toLowerCase() + '>');
  }
  document.querySelectorAll('canvas').forEach((c, i) => {
    if (!vis(c)) return;
    const id = c.id || 'canvas#' + i, r = c.getBoundingClientRect();
    if (r.width < 1 || r.height < 1 || !c.width || !c.height) { out.canvas.push(id + ' has zero size'); return; }
    try {
      const t = document.createElement('canvas'); t.width = c.width; t.height = c.height;
      const x = t.getContext('2d'); x.drawImage(c, 0, 0);
      const d = new Uint32Array(x.getImageData(0, 0, t.width, t.height).data.buffer);
      if (d.every(v => v === d[0])) out.canvas.push(id + ' is blank');
    } catch (e) { /* tainted or non-2d canvas: not checkable */ }
  });
  out.katex = document.querySelectorAll('.katex-error').length;
  out.overflow = document.documentElement.scrollWidth - document.documentElement.clientWidth;
  return out;
}"""
SNAP = r"""e => e.tagName === 'CANVAS' ? e.toDataURL() : (/^(INPUT|SELECT|TEXTAREA)$/.test(e.tagName) ? e.value : e.textContent.trim())"""


def die(msg: str, code: int = 2) -> None:
    print(f"qa: {msg}", file=sys.stderr)
    sys.exit(code)


def ensure_playwright(argv: list[str]):
    try:
        import playwright.sync_api as api
        return api
    except ImportError:
        pass
    hint = "Install uv (https://docs.astral.sh/uv/getting-started/installation/) or `pip install playwright` in a virtual environment."
    cmd = ["uv", "run", "--no-project", "--with", "playwright", "python", str(Path(__file__).resolve()), *argv]
    if os.environ.get("QA_UV") or not shutil.which("uv"):
        die("the playwright module is missing. " + hint)
    if subprocess.run(cmd[:-len(argv) - 1] + ["-c", "import playwright"], capture_output=True).returncode:
        die("uv could not provide playwright (offline?). " + hint)
    sys.exit(subprocess.call(cmd, env={**os.environ, "QA_UV": "1"}))


def cached_chromium() -> str | None:
    """Newest Chromium (headless shell preferred at equal revision) in an existing Playwright cache."""
    bases = [Path(c).expanduser() for c in CACHES] + ([Path(os.environ["LOCALAPPDATA"]) / "ms-playwright"] if os.environ.get("LOCALAPPDATA") else [])
    found = []
    for base in bases:
        for pat in ("chromium_headless_shell-*/*/chrome-headless-shell*", "chromium-*/*/Chromium.app/Contents/MacOS/Chromium",
                    "chromium-*/*/chrome", "chromium-*/*/chrome.exe"):
            for p in base.glob(pat):
                rev = next((int(m[1]) for part in p.parts if (m := re.fullmatch(r"chromium(?:_headless_shell)?-(\d+)", part))), 0)
                if p.is_file() and p.suffix in ("", ".exe"):
                    found.append((rev, "shell" in p.parts[-3], str(p)))
    return max(found)[2] if found else None


def launch(pw):
    try:
        return pw.chromium.launch(headless=True)
    except Exception as exc:
        exe = cached_chromium()
        if not exe:
            die("no Chromium available. Run: python3 -m playwright install chromium  "
                f"(or: uv run --no-project --with playwright python -m playwright install chromium)\n{str(exc).splitlines()[0]}")
        return pw.chromium.launch(headless=True, executable_path=exe)


def load_steps(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    try:
        steps = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"viz/qa.json is not valid JSON: {exc}")
    if not isinstance(steps, list):
        die("viz/qa.json must be a list of steps")
    for i, s in enumerate(steps):
        where = f"viz/qa.json step {i + 1}"
        if not isinstance(s, dict) or not isinstance(s.get("name"), str) or not isinstance(s.get("do"), list) or not s["do"]:
            die(f"{where}: needs a string \"name\" and a non-empty \"do\" list")
        if set(s) - {"name", "do", "expect"}:
            die(f"{where}: unknown key(s) {sorted(set(s) - {'name', 'do', 'expect'})}")
        for j, a in enumerate(s["do"]):
            verb = [k for k in VERBS if isinstance(a, dict) and k in a]
            if len(verb) != 1 or set(a) - {verb[0], *VERBS[verb[0]]}:
                die(f"{where} do[{j}]: use one verb of {sorted(VERBS)} plus its keys ({', '.join(f'{k}: {v}' for k, v in VERBS.items())}); got {a}")
            if any(k not in a for k in VERBS[verb[0]] if not (verb[0] == "press" and k == "on")):
                die(f"{where} do[{j}]: \"{verb[0]}\" also needs {list(VERBS[verb[0]])}")
            if verb[0] == "drag" and not all(isinstance(a[k], list) and len(a[k]) == 2 for k in ("from", "to")):
                die(f"{where} do[{j}]: drag \"from\" and \"to\" are [fx, fy] fractions")
        for j, e in enumerate(s.get("expect", [])):
            if not isinstance(e, dict) or not ("changed" in e or ("text" in e and "matches" in e)):
                die(f"{where} expect[{j}]: use {{\"changed\": SEL}} or {{\"text\": SEL, \"matches\": REGEX}}")
            if "matches" in e:
                try:
                    re.compile(e["matches"])
                except re.error as exc:
                    die(f"{where} expect[{j}]: bad regex: {exc}")
    return steps


class Runner:
    def __init__(self, browser, out: Path, prefix: str, report: list):
        self.browser, self.out, self.prefix, self.report, self.views, self.shots = browser, out, prefix, report, [], []

    def run(self, scenario, url, width, work):
        ctx = self.browser.new_context(viewport={"width": width, "height": 900}, reduced_motion="reduce")
        page, errs, probs = ctx.new_page(), [], []
        self.shots = []
        page.set_default_timeout(3000)
        page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
        page.on("console", lambda m: m.type == "error" and "favicon" not in m.location.get("url", "") and errs.append(f"console: {m.text}"))
        page.on("requestfailed", lambda r: r.url.endswith((".md", "favicon.ico")) or errs.append(f"request failed: {r.url}"))
        page.on("response", lambda r: r.status >= 400 and not r.url.endswith("favicon.ico") and errs.append(f"HTTP {r.status}: {r.url}"))
        t0 = time.time()
        try:
            page.goto(url)
            try:
                page.wait_for_selector(".katex", state="attached", timeout=4000)
            except Exception:
                pass
            page.wait_for_timeout(300)
            work(page, probs, lambda label: self.sweep(page, label, probs, errs))
        except Exception as exc:
            probs.append(f"{type(exc).__name__}: {str(exc).splitlines()[0]}")
        self.finish(page, scenario, width, probs + errs, t0)
        ctx.close()

    def sweep(self, page, label, probs, errs):
        r = page.evaluate(SWEEP)
        probs += [f"{label}: raw math {x}" for x in r["raw"]] + [f"{label}: {x}" for x in r["canvas"]]
        if r["katex"]:
            probs.append(f"{label}: {r['katex']} .katex-error")
        if r["overflow"] > 0 and label == "page":
            probs.append(f"horizontal overflow by {r['overflow']}px")

    def shot(self, page, scenario, width, full=True):
        path = self.out / f"{self.prefix}-{scenario}-{width}.png"
        page.screenshot(path=str(path), full_page=full)
        self.shots.append(path.name)

    def finish(self, page, scenario, width, probs, t0):
        try:
            self.shot(page, scenario, width)
        except Exception as exc:
            probs.append(f"screenshot failed: {exc}")
        self.report.append({"scenario": scenario, "width": width, "ok": not probs, "problems": probs, "screenshots": self.shots})
        print(f"{'PASS' if not probs else 'FAIL'}  {scenario:<28} {width:>5}px  {time.time() - t0:4.1f}s")
        for p in probs:
            print(f"        - {p[:300]}")



def page_work(runner, scenario, width):
    def work(page, probs, sweep):
        sweep("page")
        play = page.query_selector("#play")
        if play and play.get_attribute("aria-pressed") == "true":
            probs.append("reduced motion: #play is pressed on load (autoplay)")
        for view in runner.views:
            page.click(f'.sheet-nav a[data-view="{view}"]')
            page.wait_for_selector(".reader-overlay.open")
            try:
                page.wait_for_function("document.querySelector('.markdown-body')?.textContent.trim().length > 20")
            except Exception:
                probs.append(f"reader {view}: no content rendered")
            page.wait_for_timeout(250)
            sweep(f"reader {view}")
            runner.shot(page, f"{scenario}-reader-{view}", width, full=False)
            page.keyboard.press("Escape")
            if page.query_selector(".reader-overlay.open"):
                probs.append(f"reader {view}: Escape did not close it")
    return work


def step_work(step):
    def work(page, probs, sweep):
        watch = [e["changed"] for e in step.get("expect", []) if "changed" in e]
        before = {s: page.eval_on_selector(s, SNAP) for s in watch if page.query_selector(s)}
        for a in step["do"]:
            verb = next(k for k in VERBS if k in a)
            sel = a.get("on") or a[verb]
            loc = page.locator(sel).first if verb != "press" or a.get("on") else None
            if loc:
                if not loc.count():
                    probs.append(f"do {verb} {sel}: no such element in the page")
                    return
                loc.scroll_into_view_if_needed()
            if verb == "fill":
                loc.fill(str(a["value"])); loc.press("Tab")
            elif verb == "select":
                loc.select_option(str(a["value"]))
            elif verb == "click":
                loc.click()
            elif verb == "press":
                loc.press(a["press"]) if loc else page.keyboard.press(a["press"])
            else:
                b = loc.bounding_box()
                at = lambda f: (b["x"] + b["width"] * f[0], b["y"] + b["height"] * f[1])
                page.mouse.move(*at(a["from"])); page.mouse.down(); page.mouse.move(*at(a["to"]), steps=8); page.mouse.up()
        page.wait_for_timeout(150)
        for e in step.get("expect", []):
            if any(not page.query_selector(e.get(k, "body")) for k in ("changed", "text")):
                probs.append(f"expect {e}: no such element in the page")
            elif "changed" in e and page.eval_on_selector(e["changed"], SNAP) == before.get(e["changed"]):
                probs.append(f"expect changed {e['changed']}: unchanged after the step")
            elif "matches" in e:
                got = page.eval_on_selector(e["text"], "e => e.textContent.trim()")
                if not re.search(e["matches"], got):
                    probs.append(f"expect text {e['text']} matches /{e['matches']}/: got {got[:80]!r}")
        sweep("step")
    return work


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, help="screenshot/report directory (default ../<topic>-qa)")
    ap.add_argument("--widths", default="1440,390", help="comma-separated viewport widths")
    ap.add_argument("--no-file", action="store_true", help="skip the file:// run")
    a = ap.parse_args()
    try:
        widths = [int(w) for w in a.widths.split(",")]
    except ValueError:
        ap.error("--widths takes integers such as 1440,390")
    pages = sorted((ROOT / "viz").glob("*.html"))
    if not pages:
        die("no viz/*.html here; run from the topic root")
    steps = load_steps(ROOT / "viz" / "qa.json")
    sync_api = ensure_playwright(sys.argv[1:])
    out = (a.out or ROOT.parent / f"{ROOT.name}-qa").resolve()
    out.mkdir(parents=True, exist_ok=True)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    handler.func.log_message = lambda *args: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    report: list = []
    t0 = time.time()
    with sync_api.sync_playwright() as pw:
        browser = launch(pw)
        for page_file in pages:
            prefix = ROOT.name if len(pages) == 1 else f"{ROOT.name}-{page_file.stem}"
            runner = Runner(browser, out, prefix, report)
            runner.views = re.findall(r'<a[^>]*data-view="([^"]+)"', page_file.read_text(encoding="utf-8"))
            runner.views = [v for v in dict.fromkeys(runner.views) if v != "experiment"]
            http_url = f"http://127.0.0.1:{server.server_port}/viz/{page_file.name}"
            for i, width in enumerate(widths):
                for proto, url in (("http", http_url), ("file", page_file.as_uri())):
                    if proto == "file" and (a.no_file or i):
                        continue
                    runner.run(proto, url, width, page_work(runner, proto, width))
                for s in steps:
                    runner.run("step-" + re.sub(r"[^A-Za-z0-9]+", "-", s["name"]).strip("-").lower(), http_url, width, step_work(s))
        browser.close()
    server.shutdown()
    failed = [r for r in report if not r["ok"]]
    (out / "qa-report.json").write_text(json.dumps({"topic": ROOT.name, "ok": not failed, "runs": report,
        "not_observable": ["reduced-motion autoplay is checked only through #play[aria-pressed]"]}, indent=2) + "\n", encoding="utf-8")
    print(f"\nqa: {len(report) - len(failed)}/{len(report)} runs passed in {time.time() - t0:.1f}s; screenshots and qa-report.json in {out}")
    print("qa: reduced-motion autoplay is only observable through #play[aria-pressed]; look at the screenshots for the rest.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
