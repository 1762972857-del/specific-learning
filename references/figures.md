# Static figures and figure reading

Figures support specific claims in the notes. Set no figure quota; generate no surfaces, slices, differences, or convergence plots by default. `examples/*/viz/figures.py` (taylor-expansion, newton-viscosity) show figures generated from their models; keep only the relevant calls. Styling: [recipe.md](recipe.md#9-static-figures).

## Selection and generation

- Geometry: objects, transformations, key sections. Physics: motion, fields, waveforms, energy relationships. Statistics: distributions, samples, intervals. Pick what best supports the claim.
- One claim per figure, with conditions in the title/caption.
- Use `save(fig, name, numbers)` where the figure script provides it, recording key values in `figures/figures.json`. Notes cite those values, not independently typed defaults.
- Error plots only for approximation/convergence tasks. Skip a figure that adds no understanding, or when only HTML/Markdown is requested, and remove its image references.
- Pass line styles by keyword, `ax.plot(xs, ys, ls=LINES["dash"])`: a dash tuple cannot take the third positional argument, which expects a format string.

## Fonts and offline images

Before generating the full figure set, choose installed fonts covering the actual labels and check the glyphs; repeat when the font or character set changes. For Chinese, candidates include PingFang SC, Arial Unicode MS, Noto Sans CJK SC, Microsoft YaHei. A font's presence does not establish coverage of every minus sign, subscript, or character. For matplotlib:

```python
from matplotlib import font_manager
from matplotlib.ft2font import FT2Font
font = FT2Font(font_manager.findfont("PingFang SC", fallback_to_default=False))
labels = "\u6d4b\u2212\u2084\u221a\u2260\u2192\u03b8"  # Representative glyphs; use actual labels.
missing = [ch for ch in labels if not font.get_char_index(ord(ch))]
print("missing:", missing)
```

If glyphs are missing, choose a covering installed font, use math typesetting, or use plain labels such as `P4` and `1e-3`. Do not suppress warnings to hide missing-glyph boxes.

Reuse the verified font setup across the topic's figures. Keep labels concise and longer explanations in captions; inspect generated figures for cropping and collisions during acceptance. A readable fallback font needs no aesthetic replacement.

`bundle_notes.py` embeds PNG and SVG files under `viz/figures/` as data URLs; rebundle so figures appear when the HTML is opened directly. External SVG fonts, scripts, and images are not embedded; use trusted, self-contained figures. Image format alone does not establish `file://` compatibility.

## Note markers

Notes and pages may be in any language (left-to-right scripts only). `check.py` finds required sections by these invisible HTML comments, never by wording; WARN when one is missing:

| Marker | Place |
| --- | --- |
| `<!-- sl:scope -->` | Under the units/scope heading |
| `<!-- sl:pitfalls -->` | Under the pitfalls heading |
| `<!-- sl:predict -->` | Under the prediction heading |
| `<!-- sl:reading -->` | Before each figure-reading block; one per figure |

## Figure-reading blocks

After each figure in the notes, put `<!-- sl:reading -->` and then:

```markdown
**Reading the figure**
- What to inspect: the relevant line, object, region, or relationship.
- Reading: quantities and units from figures.json; state when a schematic is not to scale.
- Conclusion: the supported claim and conditions, with a source/derivation label.
- Pitfall: the most likely misreading or approximation.
```

Account for perspective, axis scales, logarithmic axes, color normalization, sampling fluctuations, rounding, and reconstructed versus original figures.

## Measured data

Keep raw data in `viz/data/*.csv`. State units and sources in headers or accompanying documentation; explain calculated-column formulas. Distinguish measured points, fitted curves, and extrapolation; correlation and causation; precision and accuracy; validated coverage and extrapolation. State whether error bars show standard deviation, standard error, or confidence intervals.
