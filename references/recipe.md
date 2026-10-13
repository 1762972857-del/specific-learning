# Visual recipe: drawing paper

**The page is a drawing sheet, ink carries the data, and color marks attention.** The recipe fixes color meanings, line styles, dimensions, viewports, and readouts, not composition (§6). User layout and color choices take precedence. Keep the full sheet shell (§4.1) unless a minimal prototype or model-only check is requested.

## 1. Required conventions

1. **Color tokens:** write `var(--…)` in pages; literal colors live only in draft.css's `:root`. `figures.py` uses the same palette.
2. **Series by line style:** solid, dashed, dotted, chain. Label line ends directly, not in detached legends.
3. **Fixed axes:** limits are constants, never recalculated from current samples; comparing parameters does not rescale. For ranges spanning orders of magnitude, offer explicit range presets (2.5/5/10) and label the current range.
4. **Honest scale:** geometry, optics, and vectors use equal coordinates, `Draft.frame(..., {equal:true})`. Mark non-scaled schematics **NTS (not to scale)**. Label one-direction magnification “vertical ×N,” not “scale 1:N.”
5. Keep `:focus-visible` visible.

## 2. Palette

| Token | Value | Meaning |
| --- | --- | --- |
| `--paper` / `--paper-2` | `#ECEAE3` / `#E3E0D6` | Paper / secondary background |
| `--ink` | `#1B1B19` | Data, axes, body text |
| `--ink-2`, `--ink-3`, `--ink-4` | Ink at 66%, 32%, 14% | Secondary text / frames and separators / registration marks and faint fills |
| `--accent` / `--accent-ink` | `#D4572A` / `#B4441C` | **Vermilion: current selection**; cursors, probes, handles, current state, selected tab; use `--accent-ink` for text |
| `--accent-wash` | Vermilion at 22% | Positive end of signed ramps |
| `--fog` / `--fog-wash` | `#8FA8BF` / fog-blue at 30% | **Fog-blue: regions**; forbidden regions, confidence bands, integration areas, resonance halos |

- Keep vermilion plus fog-blue to roughly 5% of the scene, with each meaning consistent across the page. Name colors by role (“vermilion cursor,” “fog-blue region”).
- **Color must not imply motion direction, energy loss, or causality.** Transmitted waves keep their color as amplitude decreases.
- **Fields/heatmaps:** `Draft.ramp(u)` for one-sided quantities (paper to ink); `Draft.signed(u)` for signed quantities (fog-blue through paper to pale vermilion). With signed ramps, mark the selection with an ink `Draft.cross` and label both ramp ends in the readouts.

## 3. Typography

Font stacks are draft.css `:root` tokens: `--title` (hero), `--serif` (body), `--sans` (labels, controls), `--mono` (numbers, drawing identifiers). Reuse these stacks and sizes before introducing topic-specific overrides. Keep canvas labels short; put long explanations and full formulas in captions or readouts. `Draft.text()` does not wrap or avoid collisions automatically.

| Role | Setting |
| --- | --- |
| Hero title | `--title`, 700, `clamp(40px, 7.2vw, 108px)`; optional `.ch` spans per word/character settle on load; `.latin` for Latin-only titles |
| Subtitle | `--serif`, 0.32em letter spacing, `--ink-2` |
| Body | 16px/1.65 `--serif`; lead at most 58ch |
| Viewport/panel heading | 600 12.5px `--sans`, preceded by a square letter `.tag` |
| Small labels | 600 10–11px `--sans`, 0.08–0.16em letter spacing |
| Numbers | `--mono`, `tabular-nums`; principal readout 22px |
| Canvas text | Ticks: 11px `--mono`; axis labels: 11px `--sans`; curve labels: italic 12px `--serif` |

Title fonts may fall back to SimSun on Windows.

## 4. Drawing-sheet components

### 4.1 Shared shell

- `.sheet` frame and `.zones` registration divisions, 6–1/E–A, hidden below 980px.
- `.sheet-head`: drawing identifier `SL · XX-01`, subject, `.sheet-nav` tabs `01 Experiment / 02 Guide / 03 Source` (Source only with uploaded originals, [ingest.md](ingest.md)).
- `.section-label`: dividers such as `01 EXPERIMENT · …`.
- `.sheet-foot`: dependency/verification description with `data-shell-status`.
- `.reader-overlay`: tab `data-view` values match `MARKDOWN_NOTES` keys.

### 4.2 Viewports, readouts, and controls

- **Viewport**, `figure.vp`: 1px ink border, no rounding or shadow; the letter tag in `figcaption` interrupts the border. Height via `--h`. Use viewport identifiers in captions, notes, and readouts.
- **Readout board**, `.titleblock`: 1px gaps separate cells. Principal observables first in `.key`, then auxiliary values and errors; checks in smaller `.ok`/`.fail` cells with ✓/✗, not headline values. Add scale, assumptions, or drawing identifiers when useful.
- **Parameter table**, `.params`: one quantity per cell, bound via `data-param`; `.presets` holds numbered preset buttons. Headings that interrupt the frame border stay short and single-line; detailed descriptions go inside the frame so wrapping cannot cover the first variable.
- **Control rail**, `.experiment-layout > .control-rail`: the only parameter table, left of desktop plots, sticky, independently scrollable, and beside long plots (sticky is bounded by its parent). `.experiment-main` holds views/readouts. Below 760px, controls precede plots without covering them.
- **Explanation cards:** NOTES, Markdown tables, and static figures use 14px corners and subtle contact shadows from ink tokens. Lettered viewports, derivation panels, parameter/construction frames, and readout boards stay square with ink borders; do not round every container.
- **Markdown table cards:** the table keeps native layout and `width:100%`; an outer `.table-card` owns rounded clipping, border, shadow, and horizontal scrolling. Short tables fill the card; wide tables scroll inside it, keyboard-accessible, with table semantics intact. Never set `display:block` on a table: its outer width then exceeds its rows.
- **Ruler slider**, `input.ruler`: hairline track, cursor-shaped thumb; `Draft.rulers()` adds ticks. Both endpoints stay inside the frame.

### 4.3 Canvas drawing marks, `Draft.*`

| Mark | Use |
| --- | --- |
| `WEIGHT.fine` 0.75 / `axis` 1 / `data` 2; occasional `bold` 2.6 | Dimensions/leaders lighter than axes, axes lighter than data; frames thinner than data |
| `axes(..., {grid})` | Outward ticks; faint registration crosses, not decorative full grids. `grid:false` when a grid is itself the object studied; `origin:true` puts axes through the origin |
| `DASH.chain` | Symmetry/center/equilibrium/section lines |
| `dimH` / `dimV` | Meaningful lengths/differences: barrier width, period, V₀−E, amplitude |
| `leader` | Label a curve/point directly with its reading |
| `detail` | Magnification circle; name the enlarged direction |
| `path` / `poly` | Polylines / closed polygons; both take `dash` (a `DASH.*` pattern), `poly` also `fill`, `stroke`, `width` |
| `vector` | Vectors/forces; arrowheads shrink with length |
| `cross` | Draggable or reference points |
| `dot` | Current state, filled vermilion; comparison points, hollow |
| `text` | Paper-colored outline keeps labels legible |

**Projection alignment:** align only views sharing a physical quantity (vertically aligned x axes, a main/side energy axis), never unrelated time/frequency axes. Draw cross-viewport projection lines dashed, static, and labeled (“same E”). They are not trajectories and do not flow; side views are not spatial regions. Omit them on narrow screens and stack the views.

## 5. Interaction and motion

- **Dragging:** generous hit areas; ink cross or vermilion handle.
- **Evolution:** `Draft.clock({dt, rate, step, render})` advances fixed model steps; screen refresh sets only how many run per frame. Offer play/pause, step, and reset ([rules](interpretation.md#evolution-approximation-and-sampling)).
- **Reduced motion:** disable autoplay, show the settled decorative state, keep manual operations.
- **Entrances:** decorative CSS only (`.ch` title spans, `.fade` panels); no parallax, pointer-following, or continuous loops. Small interface changes: CSS transitions of 0.2–0.42s.

## 6. Topic-specific composition

- The main view serves the learning goal and may take the full width: one large equal-scale canvas for fields and geometry; recording and fitting for measurement.
- Use `.drawing.cols-side`, `.cols-even`, or `.joined`, or topic-specific `grid-template-areas`, keeping the narrow-screen single column. Do not redundantly override shared column widths; if custom widths are needed, restore one column at the narrow-screen breakpoint.
- Reuse a suitable existing composition when it serves the topic; custom composition remains available when the learning goal needs it. Resolve crowding by moving explanations outside the canvas or stacking views before reducing text size. Use the [acceptance criteria](acceptance.md#what-blocks-delivery) to distinguish required repairs from optional polish.

## 7. Hero construction

The hero is the title with a separate ASCII drawing, never painted over it: art right of the title on desktop, stacked below on narrow screens. Characters and vermilion spans live in the topic HTML; no runtime generator.

```html
<section class="hero">
  <div class="hero-title"><p class="sub">Subtitle</p><h1>Title</h1><p class="lede">Learning goal</p></div>
  <figure class="hero-ascii" role="img" aria-label="Schematic weighted sum of two column vectors">
    <pre aria-hidden="true">     /888/<span class="ascii-accent">888/</span>
    /888/<span class="ascii-accent">888/</span>
   +---<span class="ascii-accent">---+</span></pre>
    <figcaption>Column-vector composition · schematic · NTS</figcaption>
  </figure>
  <aside class="sheet-notes" aria-label="Model notes"><h2>NOTES</h2><ol><li><div>Model assumptions; input <span data-tex="x"></span></div></li></ol></aside>
</section>
```

Only the `pre` must be printable ASCII; the title, `figcaption` and `aria-label` may be in any language. Right-to-left scripts are unsupported. Use printable ASCII and spaces, preferably within 64 columns/32 lines; ink, with `span.ascii-accent` for vermilion. No tabs, wide characters, ANSI escapes, or looping animation; escape `&`, `<`, `>`. Relate the drawing to the topic: state defaults for sampled art, label constructions schematic, mark projections/unequal scales NTS, never present art as live readings. Explain it with `aria-label`; hide `pre` from assistive reading.

## 8. Visual conventions by learning pattern

| Pattern | Convention |
| --- | --- |
| Relationships/comparison | Dashed/dotted comparisons, solid current curve |
| Geometry/transformation | Thin dashed originals, solid transformed objects, crosses on draggable points |
| Fields | `ramp`/`signed` ramps or vectors; no decorative grid |
| Evolution | `Draft.clock`; vermilion time cursor |
| Superposition | At most four line styles; for more components, stack small plots sharing an x axis instead of adding colors |
| Approximation/iteration | Log–log only where the data and error relationship suit it (applicable error regime); observed-order slope triangle with dimensioned legs |
| Randomness/statistics | Fog-blue confidence bands; repeated trials as faint `--ink-4` lines; seed in readouts |
| Measurement/inference | Residual plot directly below the main plot, shared x axis; label synthetic data SYNTHETIC |
| Pure math | Object type/domain in the units cell; dimensions for abstract lengths, NTS where applicable |

## 9. Static figures

`examples/taylor-expansion/viz/figures.py` demonstrates the matplotlib styling: paper background, ink lines, left/bottom axes only, outward ticks, no decorative grid, line-style series, vermilion current points, lettered tags (`tag()`), dimensions (`dim()`).

- Follow textbook axis conventions; when a page rotates a view (a T(E) side view), state that it is the same curve with swapped axes.
- No `plt.xkcd()` or jittered lines: drafting is precise.
