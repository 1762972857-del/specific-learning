# Teaching design

Start with a one-sentence learning goal: what the reader manipulates, observes, and can explain. Choose a primary and supporting patterns, then generate model, readouts, and notes for the actual topic. Patterns are construction principles, not course chapters or a fixed layout.

## Choosing a pattern

| Pattern | Math / physics examples | Views and operations | Observations and checks |
| --- | --- | --- | --- |
| Relationships and condition comparison | Function families, extrema, counterexamples / equations of state, resonance, tunneling | Evaluate chosen parameters directly; link curves, probes, comparisons; mark valid intervals | Special values, condition boundaries; no time animation in place of parameter comparison |
| Geometric construction and transformation | Vectors, matrices, integration regions / force resolution, trajectories, geometric optics | Drag points or objects; show coordinates, constraints, before/after; choose dimensions for the spatial relationship | Geometric/algebraic relationships, scale; distinguish schematic and scaled drawings |
| Fields and local/global relationships | Gradient, divergence, curl, integrals / electromagnetic, temperature, velocity fields | Samples, vector fields, or contours with probes, sections, integration boundaries | Local values, integral relationships; compute 2D boundary line integrals separately from 3D surface flux |
| Time evolution | ODEs, phase portraits / oscillation, circuit transients, diffusion | Set initial conditions; link curves and state views; playback, pause, step, reset when useful | Initial conditions, analytic special cases, step-size effects, conservation or balance; separate parameters, state, numerical step |
| Superposition and decomposition | Fourier methods, convolution, eigenmodes / interference, beats, standing waves | Show components and combination; adjust coefficients/phases; link time and frequency views | State what is superposed and the assumptions; distinguish complex amplitude, intensity, probability density |
| Approximation and iteration | Difference quotients, Riemann sums, Taylor expansion, root finding / small-angle approximations | Compare target and approximation; vary terms, partitions, iterations, step size; mark validity | Fix comparison target and error definition; check stability/convergence only when the goal concerns an algorithm |
| Randomness and statistics | Distributions, sampling, random walks / thermal motion, decay | State seed, sample count, resampling; show samples, distributions, repeated outcomes | Theoretical values, intervals, fluctuations; one sample need not equal the theory |
| Measurement and inference | Regression, parameter estimation, uncertainty propagation / measuring gravity, wavelength | Separate theory, observations, estimates; record data, fit, show residuals and uncertainty | Sources, units, ranges, error-bar meanings; label synthetic data |

## Course routes

Pick the archetype (table below) by the subject's emphasis, then adapt. Templates (`templates/<name>/`) are layout and drawing starting points, not content sources. Routes are examples, not a boundary; any topic in scope may start from the closest archetype or a blank sheet.

| Course area | Teaching emphasis | Primary pattern(s) | Archetype | Watch for |
| --- | --- | --- | --- | --- |
| Calculus (limits, approximation, error vs parameter) | Target vs approximation, error as a function of a parameter | Approximation; relationships | Parameter curve | Fixed axes; error definition; log-log only in a valid regime |
| Series & numerical methods | Partial sums, step size, convergence, stability | Approximation and iteration | Parameter curve (`drawRuns` for partial sums; observed-order slope triangle) | Gibbs behaviour; rounding-noise floor; no convergence plot unless asked |
| Multivariable / vector calculus | Surfaces, sections, gradients, local vs global | Fields; geometry | Surface | 3D only when the spatial relationship needs it; 2D boundary integrals vs 3D flux |
| Linear algebra | Basis vectors, grid mapping, area scaling | Geometry and transformation | Draggable geometry | Equal scale; dashed originals, solid images; determinant sign shows in both fill and arc direction |
| ODEs & mechanics | Initial conditions, state vs time, phase views | Time evolution | Time evolution | Parameters vs state vs step size; reset and pause rules; no undeclared damping |
| Waves & quantum 1D | Piecewise regions, superposition, probability | Superposition; relationships | Superposition | Density vs complex amplitude; not classical trajectories |
| Optics & interference (double slit, diffraction) | Path difference, superposition, screen intensity | Superposition; fields | Field | Amplitude vs intensity; NTS on schematic; exact superposition and the far-field formula diverge unless y << L and L >> d^2/lambda, so state which one is drawn |
| Electrostatics & fields | Potential, field lines, local values | Fields | Field (replace the field function with the potential via `Draft.signed`; add `Draft.vector` arrows) | Signed ramp for potential; arrows are direction, not magnitude |
| Circuits | Transients; DC network topology and readouts | Time evolution; relationships | Transients: time evolution. DC networks: schematic + readouts, `Draft.leader` labels | Time constant vs step; sign conventions and units |
| Thermodynamics / statistical | State variables, processes, fluctuations | Relationships; randomness | State diagram: parameter curve with fixed axes. Fluctuations: sampling. Processes over time: time evolution | Equilibrium vs process; ensemble vs single sample |
| Probability & statistics | Seed, repeated trials, confidence bands | Randomness and statistics | Sampling | A single sample need not match theory |
| Physics experiments / measurement | Theory vs observation vs fit; uncertainty | Measurement and inference | Measurement | Label synthetic data SYNTHETIC; units and error-bar meaning |

### Outside these routes

1. Write the one-sentence learning goal.
2. Classify the state the reader manipulates; scaffold from that row's template and keep its pieces.
3. Delete unrelated views, parameters, and checks. Record the mapping (which template piece shows which quantity) in the notes' scope section.
4. Beyond confident knowledge, take CHECK_CASES expectations from independent references, cite them in the notes, and state scope and assumptions.

| Archetype | Template | Keep | Add |
| --- | --- | --- | --- |
| Parameter curve (family comparison) | `taylor-expansion` | `MODEL.evaluate`, `drawRuns`, draggable point, `Draft.dimH/dimV` error marks | Fixed axes |
| Draggable geometry, equal-scale mapping | `linear-transform` | `drawPlane` (`Draft.frame(..., {equal:true})`, `Draft.drag`), `drawCircleImage`, `orientationArc` | Dashed originals, solid images |
| Field (2D heatmap with probe) | `double-slit` | `drawField` (`Draft.ramp` for magnitude, `Draft.signed` for sign, cached offscreen canvas), `drawProfile`, `drawGeometry` | `Draft.vector` arrows for direction |
| Time evolution | `newton-viscosity` | `Draft.clock`, schematic `drawA`, `drawB`, `Draft.vector` | Pause and reset rules |
| Superposition, piecewise components | `barrier-tunneling` | `MODEL.wave` (piecewise by region), `drawB` | At most four line styles |
| Surface z=f(x,y) | `partial-derivatives` | `Surface3D.draw`, `drawSlice`, `drawDiscrete` | None |
| Sampling, repeated trials | `taylor-expansion` | `drawRuns` for each trial | [recipe.md section 8](recipe.md#8-visual-conventions-by-learning-pattern) Randomness: seed readout, faint repeated trials, fog-blue bands |
| Measurement, fit with residuals | `taylor-expansion` | `MODEL.evaluate` as theory, `drawRuns` | Recipe section 8 Measurement: residual plot below, shared x; label synthetic data SYNTHETIC |

## Math and physics explanations

- **Math:** object types, domains, conditions, derivations or counterexamples, approximation error. Finite plots, cases, and numerical experiments do not replace proof. Do not call every mathematical object dimensionless.
- **Physics:** objects and situations, units and directions, assumptions, initial/boundary conditions, observables, conservation/balance, failure limits. Explain arrows, waveforms, line styles, colors, animation speed.
- **Mixed topics:** reuse computational methods; explain parameter mappings and checks separately (oscillators and RLC circuits share an equation form, not units, observables, or energy interpretation).
- **Consistency:** page, figures, numbers, and notes share definitions and defaults; symbols, pictures, values, and wording identify one another.
- **Visual honesty:** fixed axes and honest scale ([recipe.md](recipe.md#1-required-conventions)) stop an unchanged-looking curve from hiding a changing scale.

## Conditional modules

Add sliders, limits, discrete approximations, convergence plots, observed order, and 3D surfaces only when the learning goal needs them. Use 3D only when spatial relationships require it; add no surface slices or partial-derivative readouts without a surface. An inapplicable module is not a missing deliverable.

## Evolution, approximation, and sampling

- Analytic evolution may evaluate a requested time directly; numerical evolution advances state. Separate physical step size from screen refresh. Specify pause, reset, parameter-change, and background-resume behavior; none may silently change the model. Add no undeclared damping or interpolation.
- A limit does not require a convergence plot. Explain discontinuities and Gibbs behavior for Fourier partial sums; do not promise pointwise vanishing peak error.
- Estimate observed order only for positive errors in a valid regime expected to satisfy `e(h) ≈ C h^p`. Fix the endpoint or norm, state the refinement ratio and theory, and report estimates as unavailable at rounding noise, zero error, or instability.
- Distinguish a distribution, a single realization, and a measured sample. State seeds and sample counts; show repeated outcomes and intervals, not zero error from one realization. Do not present quantum probability plots as classical trajectories.

## Verification, provenance, and prediction tasks

- **Checks:** choose what fits the model: known results, identities, initial/boundary conditions, independent algorithms, conservation/balance, or statistical intervals. State tolerances and coverage. For damped systems check balances, not conserved energy. If no computable check applies, say so; never fabricate an identically zero check.
- **Provenance labels:** tags stay English in notes of any language (`check.py` matches them literally): `[Source] (p.12)` for uploaded originals, `[Derivation]` for original reasoning, `[Standard result]` plus a source for established results, `[Inference]` for unverified judgments. Every substantive claim has a traceable source or label.
- **Pitfalls and prediction:** explain units or object types, applicability, and common pitfalls. Give a prediction task whose operation and answer are both observable on the page; no fixed count.

## Sources and reuse

Public courses support verification of common concepts and learning tasks: [MIT 18.01](https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/pages/syllabus/), [18.02](https://ocw.mit.edu/courses/18-02-multivariable-calculus-spring-2006/pages/calendar/), [18.03](https://ocw.mit.edu/courses/18-03-differential-equations-spring-2010/pages/syllabus/), [8.02 experiments](https://ocw.mit.edu/courses/8-02-physics-ii-electricity-and-magnetism-spring-2007/pages/experiments/), [8.03](https://ocw.mit.edu/courses/8-03sc-physics-iii-vibrations-and-waves-fall-2016/pages/syllabus/). The classification above is original organization.

- Verifying against public course pages and citing them with links is fine. Copying their text, figures, or exercises, or closely adapting them, is not.
- Write notes originally. Public access does not imply redistribution rights; rewording, translation, or citation does not grant permission ([WIPO copyright FAQ](https://www.wipo.int/en/web/copyright/faq-copyright)).
- Before reusing third-party text, figures, exercises, or code, check the license and retain attribution, license notices, and modification notes. MIT OCW's default [CC BY-NC-SA 4.0 terms](https://ocw.mit.edu/pages/privacy-and-terms-of-use/) are noncommercial and share-alike; do not relabel those resources with the MIT software license. Individual resource notices take precedence.
