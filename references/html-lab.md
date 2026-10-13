# Interactive lab pages

Code contracts for the lab page; visual vocabulary is in [recipe.md](recipe.md).

## Choosing a starting point

- Load only the shared files in `viz/assets/` (draft.css, draft.js, optional surface3d.js per [surface3d.md](surface3d.md), vendored KaTeX 0.19 and marked 15); draw with Canvas 2D or inline SVG. No CDN resources, frameworks, or libraries (React, Three.js, D3).
- Put shared style fixes in draft.css/draft.js, not one page or output, within the user's requested scope.

## Page regions

- `.experiment-layout` holds a left `.control-rail` (the only `.params`) and a right `.experiment-main` (plots, readouts) ([recipe.md](recipe.md#42-viewports-readouts-and-controls)).
- `Draft.shell()` wraps each rendered Markdown table in `.table-card`. To translate its UI text, run `Object.assign(Draft.strings, {table, noNotes, renderFailed, statusFile, statusHttp})` before `Draft.shell()`; reader tab titles come from `bundle_notes.py` `key=Title=path` (defaults Guide/Source).
- Cross-viewport marks may use `.drawing > canvas.plate`.
- Derivations, predictions, pitfalls, and sources go in `.notes` panels, full notes in the Markdown reader; standalone Markdown stays readable without the panel.
- Leave no empty observed-order readout cell when no convergence module applies.

## State contract

```js
const DEFAULTS = {/* Match model.py DEFAULTS and DEFAULT_INPUTS. */};
const state = {...DEFAULTS};
function update(patch = {}) { Object.assign(state, patch); Draft.syncParams(params, state); render(); }
Draft.bindParams(params, update);             // All [data-param] controls
Draft.drag(canvas, {hit, move});              // Optional: move() calls update()
const clock = Draft.clock({dt, step, render}); // Optional: time evolution
```

- One `state` per page. Controls, dragging, presets, clock, and reset change it only through `update()`; `render()` reads `state` and `MODEL` without mutating either.
- Shared controls that edit the selected item (a matrix column, token, vector) use `[data-sel="key"]`, not `data-param`. The selection is an ordinary state key (a `data-param` select or a drag); edits become `update(set(state, key, value))`, so controls never mutate state, and clamping follows min/max as in `bindParams`. Dynamically added controls work too.
  ```js
  const sync = Draft.bindSelected(params, update, {get: s => s[s.sel], set: (s, k, v) => ({[s.sel]: {...s[s.sel], [k]: v}})});
  // in update(): Draft.syncParams(params, state); sync(state); render();
  ```
- Name parameters, observation positions, initial conditions, time, numerical steps and precision, seeds and samples, and measured data separately. A simulation step is not a physical parameter; keep it out of the parameter table.
- Each control changes an explainable result. Sliders are optional; dragging, stepping, switching, or exact input can each form a complete experiment. Dragging is additional: keep the same quantity on keyboard-operable controls.

## Model interface

```js
const MODEL = {
  evaluate(inputs, P) {
    // inputs: position, time, initial conditions; P: parameters.
    // Return named finite scalars; no DOM access.
    return {value: /* topic calculation */};
  }
};
globalThis.MODEL = MODEL;
```

`MODEL` is pure functions in `<script id="lab-model">`. Python and JavaScript are separate implementations. `model.py` provides `evaluate(inputs, P)` with the same output keys, and `DEFAULTS`/`DEFAULT_INPUTS` matching the initial page state. Internals may use vectors, matrices, or evolution algorithms; expose named scalar observables (`y0`, `y1`), not arrays.

Declare independent reference cases in `model.py`:

```python
CHECK_CASES = [{
    "name": "Hand-computable case",
    "inputs": {"t": 0}, "params": {"amplitude": 1},
    "expected": {"position": 1}, "atol": 1e-9, "rtol": 1e-9,
}]
```

`expected` comes from hand calculation, an analytic result, or a trusted reference, never the function under test. `check.py` tests known results, then compares all Python/JavaScript outputs on the same cases: case verification, not proof, and agreement across languages does not replace known results. Check strategy: [interpretation.md](interpretation.md#verification-provenance-and-prediction-tasks).

Independent reference methods: `Fraction` for exact rationals; `Decimal` for separately calculated constants; finite differences with spacing balancing truncation and rounding; seeded random cases including boundaries.

For out-of-domain inputs, intervals crossing singularities, or infinite radii, keep outputs finite and add validity flags, such as `{in_domain:0, value:0}` or `{radius_finite:0, radius:0}`. Zero is a placeholder, not a result: read the flag before showing “Outside domain,” “Not applicable,” or infinity. Plotting samples may use `NaN` to break undefined segments; `NaN`/`Infinity` must not enter `evaluate` outputs or appear as zero error.

Put topic-specific invariants (conservation, residuals, convergence order) in an optional `extra_checks(report)` in `model.py`, calling `report("OK"|"ERROR"|"WARN", message)`; see `templates/barrier-tunneling/viz/model.py`. `MODEL` may expose extra drawing helpers (`f`, `wave`); only `evaluate` is compared.

## Views

- Each viewport is a `figure.vp` with `figcaption` and canvas. Give each canvas `role="img"` and `aria-describedby`; update its description in `render()`.
- `Draft.box(canvas, pad)` gives the drawing box; `Draft.frame(box, xr, yr, {equal})` gives coordinates.

## Formula markup

- Mark HTML formulas (leads, NOTES, captions, readout labels, units/scope, expanded explanations, table cells) with `data-tex` and `Draft.math()`; dynamic ones with `Draft.setMath()`. The renderer does not infer formulas from bare `P_n`, summation notation, or Unicode superscripts; do not build them from `<sub>`, `<sup>`, or Unicode powers.
- Give dynamic math its own span: `<p>Near the expansion point <span id="centre-math"></span></p>` with `Draft.setMath(centre, \`a=${state.a}\`)`. Write TeX commands with `String.raw` or doubled backslashes; use `textContent` only for plain text/numbers. Native `<option>` labels and canvas text cannot render this HTML: keep clear text there, full formulas nearby. Accessibility descriptions use natural language.
- Markdown: `$…$` inline and `$$…$$` display, in all paragraphs, lists, figure readings, and tables. Use `\lvert x\rvert` in tables. No formulas in code spans. Separate bold lead-ins from the following text (`**Coefficient formula.** Let…`) so raw asterisks do not appear.
- `.sheet-notes li` is a two-column number/body grid: wrap a body with inline formulas or several inline nodes in one `<div>`, or the nodes occupy separate cells.
- Style control labels through direct children (`label>span`); descendant rules such as `label span{display:block}` break KaTeX internals.
