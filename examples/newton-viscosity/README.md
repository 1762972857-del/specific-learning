# Newton's law of viscosity

This example is a self-contained English learning page for steady plane Couette flow. Open [`viz/newton-viscosity.html`](viz/newton-viscosity.html) through a local HTTP server or directly as a file. The page uses only local assets and runs its calculations in the browser.

The page contains:

- [`viz/newton-viscosity.html`](viz/newton-viscosity.html): the drafting-paper shell, ASCII hero, NOTES, controls, two Canvas views, readouts, KaTeX formulas, and the Markdown reader.
- [`viz/model.py`](viz/model.py): the Python model, shared defaults, and 12 independent hand-calculated cases.
- The HTML `lab-model`: an independent JavaScript implementation of velocity, gradient, stress, plate force, dissipation, power balance, displacement, and no penetration.
- [`viz/figures.py`](viz/figures.py): standard-library generation of the static velocity-profile SVG and `figures/figures.json`.
- [`notes/01-viscosity.md`](notes/01-viscosity.md): the English guide with derivation, units, predictions, pitfalls, limits, and direct sources.
- [`viz/markdown-bundle.js`](viz/markdown-bundle.js): the bundled guide used when the page is opened without a server.
- `viz/assets/`: a symlink to the shared project assets (`../../../assets`), including Draft, local KaTeX, and marked.

There is one page state object. Number inputs, range sliders, the draggable probe, presets, and the clock all update it through `update()`. `render()` reads the pure model and then redraws the A layered-flow view, the B velocity profile, the title readouts, and the accessible descriptions.

Plate speed, gap, viscosity, and area are physical parameters. Changing one pauses the clock and resets tracer time because the page switches directly to a new steady state. Moving the probe changes only the observation position. `Draft.clock` advances a fixed 0.001 s physical step; playback runs at 0.1× physical speed and the single-step button advances 0.05 s. The model uses analytic displacement $x(t)=u(y)t$, so animation does not accumulate numerical integration error.

From this directory, regenerate the figure, bundle the guide, and run the model/resource checks with:

```sh
python3 viz/figures.py
python3 viz/bundle_notes.py
python3 viz/check.py
```

The model checks cover no-slip values at both plates, rigid translation, opposite and negative shear, gap and viscosity scaling, advection, no penetration, control-limit gradients, low viscosity, and larger area. Python and JavaScript outputs are compared with absolute and relative tolerances of `1e-10`. These finite cases verify the selected inputs; they do not prove all inputs or real-flow stability.

The model assumes steady, incompressible, constant-viscosity Newtonian flow between sufficiently large plates, no pressure gradient, no slip, no wall-normal flow, and laminar behavior. It does not simulate startup, turbulence, non-Newtonian rheology, free surfaces, inlet effects, or edge effects. The 0.12 m horizontal wraparound and the vertical geometry/force arrows are viewing conventions; the latter are marked NTS (not to scale).

The guide cites the [Arnedo viscosity section](https://eng.libretexts.org/Bookshelves/Aerospace_Engineering/Fundamentals_of_Aerospace_Engineering_(Arnedo)/03%3A_Aerodynamics/3.01%3A_Fundamentals_of_fluid_mechanics/3.1.04%3A_Viscosity) and [Oregon State's Introduction to Viscous Flows](https://open.oregonstate.education/intermediate-fluid-mechanics/chapter/introduction-to-viscous-flows/).
