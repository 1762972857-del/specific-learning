"""Finite rectangular barrier scattering model.

The length unit is nm and the energy unit is eV.  For an electron,
``C = hbar**2 / (2*m_e)`` is 0.0380998211615486 eV nm².  The incoming
plane-wave amplitude is one, and the two outside regions have the same
potential and mass, so ``T = |B|²`` and ``R = |r|²``.

The browser page contains an independent JavaScript implementation.  The
known-result cases below are hand-derived or analytic limiting cases; they
are used to compare both implementations without treating either one as the
source of truth.
"""

from __future__ import annotations

import cmath
import math

C = 0.0380998211615486
DEFAULTS = {"E": 0.5, "V0": 1.0, "a": 0.5}
DEFAULT_INPUTS = {"x": 0.25}


def _validate(inputs: dict[str, float], P: dict[str, float]) -> None:
    values = [inputs["x"], P["E"], P["V0"], P["a"]]
    if not all(math.isfinite(float(v)) for v in values):
        raise ValueError("all inputs must be finite")
    if P["E"] <= 0 or P["V0"] < 0 or P["a"] < 0:
        raise ValueError("E and V0 must be non-negative with E > 0; a must be non-negative")


def cs(q_squared: float, z: float) -> tuple[float, float]:
    """Return c(z), s(z) with c'' + q²c = 0 and s(0)=0, s'(0)=1.

    The small-argument series keeps the E=V0 limit numerically stable.  It
    also avoids dividing by a tiny q when the two energies nearly match.
    """

    q2z2 = abs(q_squared * z * z)
    if q2z2 < 1e-7:
        return (
            1 - q_squared * z**2 / 2 + q_squared**2 * z**4 / 24,
            z - q_squared * z**3 / 6 + q_squared**2 * z**5 / 120,
        )
    if q_squared > 0:
        q = math.sqrt(q_squared)
        return math.cos(q * z), math.sin(q * z) / q
    if q_squared < 0:
        kappa = math.sqrt(-q_squared)
        return math.cosh(kappa * z), math.sinh(kappa * z) / kappa
    return 1.0, z


def amplitudes(P: dict[str, float]) -> tuple[float, float, complex, complex]:
    """Return k, q², transmitted amplitude B, and reflected amplitude r."""

    E, V0, a = P["E"], P["V0"], P["a"]
    k = math.sqrt(E / C)
    q_squared = (E - V0) / C
    c, s = cs(q_squared, a)
    denominator = complex(c, -(k * k + q_squared) * s / (2 * k))
    B = 1 / denominator
    r = B * complex(c, -k * s) - 1
    return k, q_squared, B, r


def wave(x: float, P: dict[str, float]) -> tuple[complex, complex]:
    """Return psi(x), psi'(x) for the matched stationary scattering state."""

    k, q_squared, B, r = amplitudes(P)
    a = P["a"]
    if x < 0:
        incoming = cmath.exp(1j * k * x)
        reflected = r * cmath.exp(-1j * k * x)
        return incoming + reflected, 1j * k * (incoming - reflected)
    if x > a:
        transmitted = B * cmath.exp(1j * k * (x - a))
        return transmitted, 1j * k * transmitted
    c, s = cs(q_squared, x - a)
    return B * complex(c, k * s), B * complex(-q_squared * s, k * c)


def evaluate(inputs: dict[str, float], P: dict[str, float]) -> dict[str, float]:
    """Return named finite observables at the requested probe position."""

    _validate(inputs, P)
    k, q_squared, B, r = amplitudes(P)
    psi, derivative = wave(inputs["x"], P)
    T = abs(B) ** 2
    R = abs(r) ** 2
    return {
        "k": k,
        "q_squared": q_squared,
        "T": T,
        "R": R,
        "balance": T + R,
        "psi_real": psi.real,
        "psi_imag": psi.imag,
        "density": abs(psi) ** 2,
        "flux_ratio": (psi.conjugate() * derivative).imag / k,
    }


# Expected values are independent analytic results.  In particular, the
# threshold cases use the continuous limit rather than evaluating a singular
# looking branch of the closed formula.
CHECK_CASES = [
    {
        "name": "zero-width free propagation",
        "params": {"a": 0},
        "expected": {"T": 1, "R": 0, "balance": 1, "density": 1, "flux_ratio": 1},
    },
    {
        "name": "zero-height free propagation",
        "params": {"V0": 0},
        "expected": {"T": 1, "R": 0, "density": 1, "balance": 1},
    },
    {
        "name": "below-barrier kappa a equals asinh(1)",
        "params": {"a": math.sqrt(C / 0.5) * math.asinh(1)},
        "expected": {"T": 0.5, "R": 0.5, "balance": 1, "flux_ratio": 0.5},
    },
    {
        "name": "threshold with k a equals 2",
        "params": {"E": 1, "V0": 1, "a": 2 * math.sqrt(C)},
        "expected": {"T": 0.5, "R": 0.5, "balance": 1, "flux_ratio": 0.5},
    },
    {
        "name": "above-barrier first resonance",
        "params": {"E": 2, "V0": 1, "a": math.pi * math.sqrt(C)},
        "expected": {"T": 1, "R": 0, "balance": 1},
    },
    {
        "name": "transmitted density equals T",
        "inputs": {"x": 2},
        "params": {"a": math.sqrt(C / 0.5) * math.asinh(1)},
        "expected": {"density": 0.5, "flux_ratio": 0.5},
    },
    {
        "name": "left-region net flux includes reflection",
        "inputs": {"x": -1},
        "params": {"a": math.sqrt(C / 0.5) * math.asinh(1)},
        "expected": {"flux_ratio": 0.5, "balance": 1},
    },
    {
        "name": "threshold approached from below",
        "params": {"E": 1 - 1e-10, "V0": 1, "a": 2 * math.sqrt(C)},
        "expected": {"T": 0.5, "balance": 1},
        "atol": 1e-8,
    },
    {
        "name": "threshold approached from above",
        "params": {"E": 1 + 1e-10, "V0": 1, "a": 2 * math.sqrt(C)},
        "expected": {"T": 0.5, "balance": 1},
        "atol": 1e-8,
    },
]


def extra_checks(report) -> None:
    """Topic-specific invariants, called by viz/check.py with its report(level, msg).

    Conservation, current normalization and interface matching across all three
    regimes (E<V0, E=V0, E>V0), in addition to the hand-derived CHECK_CASES.
    """
    sweep = [
        {"E": 0.2, "V0": 1.0, "a": 0.4},
        {"E": 1.0, "V0": 1.0, "a": 0.4},
        {"E": 2.0, "V0": 1.0, "a": 0.4},
        {"E": 0.7, "V0": 0.0, "a": 0.4},
    ]
    balance_error = 0.0
    current_error = 0.0
    for params in sweep:
        balance_error = max(balance_error, abs(evaluate({"x": 0.2}, params)["balance"] - 1.0))
        for x in (-1.0, 0.2, params["a"] + 1.0):
            row = evaluate({"x": x}, params)
            current_error = max(current_error, abs(row["flux_ratio"] - row["T"]))
    report("OK" if balance_error < 1e-9 else "ERROR",
           f"barrier conservation sweep: max |R+T-1| = {balance_error:.2e}")
    report("OK" if current_error < 1e-9 else "ERROR",
           f"barrier current sweep: max |j/j_inc-T| = {current_error:.2e}")

    interface_error = 0.0
    eps = 1e-8
    for params in sweep[:3]:
        for boundary in (0.0, params["a"]):
            left = wave(boundary - eps, params)
            right = wave(boundary + eps, params)
            interface_error = max(interface_error, abs(left[0] - right[0]), abs(left[1] - right[1]))
    report("OK" if interface_error < 1e-5 else "ERROR",
           f"interface continuity sweep: max |delta psi or delta psi'| = {interface_error:.2e}")
