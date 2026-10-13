# Acceptance

Run `python3 viz/build.py` from the topic root, then inspect the page yourself; the `0 error` line alone is not acceptance.

## What blocks delivery

| Class | Examples | Action |
| --- | --- | --- |
| Correctness and function | Failed checks, wrong numbers or formulas, broken operations, missing offline assets, misleading axes or units | Fix and verify before delivery |
| Readability and access | Missing glyphs, clipped units, labels obscuring the relevant curve, unreadable text, inaccessible controls | Fix with the simplest readable layout and verify before delivery |
| Optional polish | Uneven whitespace, an unattractive but readable title wrap, decorative proportions, minor corner or shadow differences | Leave as-is or note briefly; do not block delivery |

Keep the shared visual conventions when authoring. Optional polish does not waive script errors, semantic conventions, accessibility, or explicit user requirements. Font substitution is acceptable when all characters remain readable and layout still works.

## Checked by `viz/build.py` / `check.py`

`build.py` runs `figures.py` (if present), `bundle_notes.py`, then `check.py`; it stops at the first failing step.

- `ERROR` fails the run. `WARN` is advisory. `SKIP` means a check did not run: the two `node` checks (lab-model outputs, `DEFAULTS`) skip when `node` is missing or `--no-node` is passed.
- Read every WARN and SKIP; resolve or report it.
- A pass is case-based; it does not prove the mathematics, interaction, or presentation.

- `viz/model.py` exists; `evaluate` returns a non-empty mapping of finite scalars ([model](html-lab.md#model-interface)).
- `CHECK_CASES` is non-empty, each case with non-empty finite `expected` and non-negative tolerances; known results match; `extra_checks(report)` output is read.
- Page `lab-model` outputs match Python in names and values on every case.
- Page `const DEFAULTS` equals model `DEFAULTS` + `DEFAULT_INPUTS` on shared numeric keys; WARN if the literal is missing, not evaluable, shares no keys, or lacks a model `DEFAULTS` key ([state](html-lab.md#state-contract)).
- Page ids: static ids unique; ids used by `$('x')`, `getElementById`, `querySelector('#x')`, `for`, `aria-describedby/labelledby/controls`, `href="#x"` exist (ids the scripts create at runtime are exempt); no tag-like text inside a quoted attribute (a lost closing quote). All ERROR.
- Page, linked CSS, and `figures.py` use only draft.css palette colors ([palette](recipe.md#2-palette)).
- No external scripts, stylesheets, or `@import`; every local asset exists ([dependencies](html-lab.md#choosing-a-starting-point)).
- `section.hero` holds `figure.hero-ascii`: `role="img"`, `aria-label`, `figcaption`, and a `pre` of nonempty printable ASCII with spans only; WARN beyond 64 columns or 32 lines ([hero](recipe.md#7-hero-construction)).
- No `{{…}}` placeholders in page or notes, and no `unadapted template file` WARN.
- `markdown-bundle.js` is readable, matches notes and figure files (stale is an ERROR; run `viz/bundle_notes.py`), and has a key for each reader tab `data-view` except `experiment`.
- `notes/*.md` exist; image links resolve; at least one provenance tag (WARN) ([labels](interpretation.md#verification-provenance-and-prediction-tasks)); the `sl:pitfalls`, `sl:scope`, `sl:predict` markers (WARN each) and one `sl:reading` marker per figure (WARN) ([markers](figures.md#note-markers)).

## Inspect yourself

- Run `python3 viz/qa.py` (or `python3 viz/build.py --qa`) from the topic root. Declare the topic's interactions in `viz/qa.json` (schema in `qa.py --help`; steps run over HTTP at every width), then read `qa-report.json` and open the screenshots in `--out` (default `../<topic>-qa/`, outside the delivery). Exit 1 is a failure to fix; exit 2 means the browser run was not possible: report it and use host browser tools. Do not write per-topic browser scripts; extend `viz/qa.json`.
- Default coverage is HTTP at 1440px and 390px, plus `file://` at 1440px, all with reduced motion. With `--widths`, HTTP runs at every supplied width and `file://` only at the first. If offline behavior differs by width, add `python3 viz/qa.py --widths 390`; do not routinely duplicate the full matrix.
- Covered by `qa.py` (no need to repeat manually unless the result is suspect):
  - console and page errors, failed requests; notes load from the bundle under `file://`.
  - no horizontal overflow; no zero-size or blank canvas.
  - no `.katex-error`; no raw `$…$`, `\frac` or `**` in the page or in any reader tab.
  - every reader tab opens and Escape closes it.
  - `#play` is not pressed on load under reduced motion (other clocks are not observable).
  - the `qa.json` operations ran and the declared readouts or canvases changed.
- Still needs visual review at both widths; collect findings before editing. Use the HTTP screenshots for layout and interaction states; use the offline report/screenshots to check loading differences. Open or scroll content not visible in screenshots.
  - layout is readable and usable: controls do not cover plots, frame headings do not overlap content, slider endpoints remain accessible, table content can be reached, and hero text/art do not overlap or crop. Minor decorative differences belong to optional polish.
  - formulas read correctly: sub/superscripts, no bare `P_n` subscripts ([formulas](html-lab.md#formula-markup)), units and scope, dynamic math after updates.
  - colors, line styles, fixed or preset-labeled axes, NTS and “vertical ×N” labels follow [conventions](recipe.md#1-required-conventions); leaders join readings to objects; checks sit in small readout cells.
  - every figure: glyphs, minus signs, subscripts, cropping ([fonts](figures.md#fonts-and-offline-images)).
  - operations beyond `qa.json`: every retained operation works; plots and readings stay synchronized; dragging and exact input change one state; every parameter is keyboard-operable with visible focus ([state](html-lab.md#state-contract)); manual operation under reduced motion ([motion](recipe.md#5-interaction-and-motion)).
  - native surface: dragging and keyboard agree; overlays imply no occlusion; loads offline ([surface3d](surface3d.md#applicability)).
  - each canvas has a state-dependent text description ([views](html-lab.md#views)).

Canvas checks detect blank or zero-size drawings, not overlapping labels or clipped text inside a drawing. Inspect those directly. Exercise retained operations not covered by `qa.json`; screenshots alone cannot verify keyboard access or synchronization.

## Repair and stop

- Fix the collected correctness, function, and readability findings together. For cramped drawings, shorten labels, move explanations into captions/readouts, or stack views while preserving the required information and scale conventions. Avoid repeatedly shrinking text or nudging coordinates.
- Rebuild affected figures/bundles and rerun the relevant automated checks after repairs. Visually recheck the changed figure or region at both widths, including affected interaction states. Expand review when failures or shared changes warrant it; unchanged regions need no repeated aesthetic review. Shared asset changes follow [repository checks](../CONTRIBUTING.md#when-to-run-what).
- Stop when required checks and content gates pass, required visual/interaction review is complete, and every WARN/SKIP is resolved or reported. A skipped check is not a pass; state any unverified coverage. Reporting a known correctness, function, or readability failure does not make it acceptable.
- Unless the user asks for further refinement, allow at most one optional polish pass and do not start another redesign during acceptance. This limit applies only to polish: unresolved required findings still need repair and verification.

## Content gates

- Definitions, symbols, diagrams or situations, numbers, and explanations refer to one another ([consistency](interpretation.md#math-and-physics-explanations)).
- Domains, prerequisites, and simplifications are stated ([prerequisites](ingest.md#natural-language-questions)).
- At least one meaningful operation: dragging, exact input, switching conditions, stepping, playback, or comparing experiments.
- Checks fit the topic with stated tolerances and coverage. Units or object types, applicability, pitfalls, and a page-checkable prediction task are present ([verification](interpretation.md#verification-provenance-and-prediction-tasks)).
- No fabricated zero check.
  - Bad: a residual zero by construction, such as a function minus itself, or `T_t - a*T_xx` evaluated on the same closed form that is presented as evidence.
  - Allowed only when labeled "structural identity, not independent evidence": an equidistance or normalization identity.
  - Preferred: an independent reference such as a hand-computed case, finite differences, or a conservation law under perturbation.
- Claims carry source or derivation labels; no invented quotations, pages, or citations ([ingest](ingest.md#natural-language-questions)).
- Conditional modules (limits, convergence, observed order, 3D) appear only where they apply ([modules](interpretation.md#conditional-modules)).
- Page, model, figures, and notes share defaults; no `TOPIC:` placeholders or unused modules.
