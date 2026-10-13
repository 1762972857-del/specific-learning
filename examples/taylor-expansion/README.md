# Taylor expansion

Open [the interactive lab](viz/taylor-expansion.html). Drag degree, centre or probe to compare Taylor polynomials, tolerance intervals and errors. All assets and notes work offline. Python is only for authors regenerating figures or verifying models.

From this directory, with NumPy, matplotlib and Node available:

```sh
python viz/figures.py
python viz/bundle_notes.py
python viz/check.py
```

Alternatively use `uv run --no-project --with numpy --with matplotlib python viz/figures.py`; the checks use only Python's standard library. See `requirements.txt`.

`model.py` is the Python implementation; HTML contains a separate JavaScript implementation. `figures.py` creates three original figures and `figures.json`. `check.py` verifies independent fixed results and Python/JavaScript agreement; its `extra_checks` in `model.py` add finite-difference coefficient and random remainder-bound checks. These checks do not prove correctness for every input. Rebuild the bundle after editing notes or figures.

Sources and limits are in the Guide.
