#!/usr/bin/env python3
"""Taylor polynomials for six real elementary functions.

Separate implementation from the HTML JavaScript model. evaluate() returns finite
scalar observables for cross-language checks. in_domain, bound_ok and radius_finite
flags determine whether values apply; zero placeholders must not be displayed as
actual results. n is rounded to an integer. The omitted-term search skips up to six
zero coefficients; relative error is invalid when abs(f(x)) <= 1e-12.
Independent reference cases use high-precision decimal and exact rational sums.
"""
from __future__ import annotations

import math


FIDS = ("exp", "sin", "ln1p", "sqrt1p", "geom", "inv1px2")
ALPHA = 0.5                      # sqrt1p = (1+x)^ALPHA
N_MAX = 12
X_WINDOW = (-4.5, 4.5)
X_PROBE_RANGE = (-4.0, 4.0)
TAUS = (1e-1, 1e-2, 1e-3, 1e-4)
YMAGS = (0.5, 1.0, 2.0)
A_RANGE = {"exp": (-2.5, 2.5), "sin": (-2.5, 2.5), "inv1px2": (-2.5, 2.5),
           "ln1p": (-0.8, 2.5), "sqrt1p": (-0.8, 2.5), "geom": (-0.8, 2.5)}
Y_RANGE = {"exp": (-2.0, 12.0), "sin": (-2.0, 2.0), "ln1p": (-3.0, 2.5),
           "sqrt1p": (-1.5, 2.5), "geom": (-4.0, 4.0), "inv1px2": (-1.5, 2.5)}
SINGULARITY = {"ln1p": -1.0, "sqrt1p": -1.0, "geom": -1.0}

DEFAULTS = {"fid": "exp", "a": 0.0, "n": 4.0, "tau": 1e-2, "ymag": 1.0}
DEFAULT_INPUTS = {"x": 1.0}



def domain_ok(fid, x):
    """Whether the selected function is defined at x."""
    if fid in ("ln1p", "sqrt1p"):
        return x > -1.0
    if fid == "geom":
        return x != -1.0
    return True


def fn_value(fid, x):
    if fid == "exp":
        return math.exp(x)
    if fid == "sin":
        return math.sin(x)
    if fid == "ln1p":
        return math.log1p(x) if x > -1.0 else float("nan")
    if fid == "sqrt1p":
        return math.sqrt(1.0 + x) if x >= -1.0 else float("nan")
    if fid == "geom":
        return 1.0 / (1.0 + x) if x != -1.0 else float("nan")
    if fid == "inv1px2":
        return 1.0 / (1.0 + x * x)
    raise ValueError(f"unknown function {fid!r}")


def derivative_at(fid, a, k):
    """Analytic kth derivative at a, independent of the coefficient recurrence."""
    if fid == "exp":
        return math.exp(a)
    if fid == "sin":
        return math.sin(a + k * math.pi / 2)
    if fid == "ln1p":
        if k == 0:
            return math.log1p(a)
        return (-1.0) ** (k - 1) * math.factorial(k - 1) / (1.0 + a) ** k
    if fid == "sqrt1p":
        value = (1.0 + a) ** (ALPHA - k)
        for j in range(k):
            value *= ALPHA - j
        return value
    if fid == "geom":
        return (-1.0) ** k * math.factorial(k) / (1.0 + a) ** (k + 1)
    if fid == "inv1px2":

        d_prev, d = 0.0, 1.0 / (1.0 + a * a)
        for j in range(k):
            d_prev, d = d, -(j + 1) * (2.0 * a * d + j * d_prev) / (1.0 + a * a)
        return d
    raise ValueError(f"unknown function {fid!r}")


def coeffs(fid, a, n):
    """Taylor coefficients c_k = f^(k)(a)/k! for k = 0..n."""
    out = []
    if fid == "exp":
        ea, fact = math.exp(a), 1.0
        for k in range(n + 1):
            if k:
                fact *= k
            out.append(ea / fact)
    elif fid == "sin":
        fact = 1.0
        for k in range(n + 1):
            if k:
                fact *= k
            out.append(math.sin(a + k * math.pi / 2) / fact)
    elif fid == "ln1p":
        out.append(math.log1p(a))
        for k in range(1, n + 1):
            out.append((-1.0) ** (k - 1) / (k * (1.0 + a) ** k))
    elif fid == "sqrt1p":
        c = math.sqrt(1.0 + a)
        out.append(c)
        for k in range(n):
            c *= (ALPHA - k) / ((k + 1) * (1.0 + a))
            out.append(c)
    elif fid == "geom":
        c = 1.0 / (1.0 + a)
        out.append(c)
        for _ in range(n):
            c *= -1.0 / (1.0 + a)
            out.append(c)
    elif fid == "inv1px2":
        d = 1.0 + a * a
        prev, cur = 0.0, 1.0 / d          # c_{-1} = 0，c_0 = 1/(1+a²)
        out.append(cur)
        for _ in range(n):
            prev, cur = cur, -(2.0 * a * cur + prev) / d
            out.append(cur)
    else:
        raise ValueError(f"unknown function {fid!r}")
    return out


def poly_value(cs, a, x):
    """Evaluate by Horner on the shifted input x-a."""
    value = 0.0
    for c in reversed(cs):
        value = value * (x - a) + c
    return value


def radius(fid, a):
    """Distance to the nearest singularity; None for an entire function."""
    if fid in ("exp", "sin"):
        return None
    if fid == "inv1px2":
        return math.hypot(a, 1.0)
    return abs(a + 1.0)                    # ln(1+x)、√(1+x)、1/(1+x)


def _bound_M(fid, a, x, n):
    """Bound abs(f^(n+1)) between a and x; None when inapplicable."""
    lo, hi = min(a, x), max(a, x)
    if fid == "exp":
        return math.exp(hi)
    if fid == "sin":
        return 1.0
    if fid == "ln1p":
        if lo > -1.0:
            return math.factorial(n) / (1.0 + lo) ** (n + 1)
        return None
    if fid == "sqrt1p":
        if lo > -1.0:
            beta = 1.0
            for j in range(n + 1):
                beta *= ALPHA - j
            return abs(beta) * (1.0 + lo) ** (ALPHA - n - 1)
        return None
    if fid == "geom":
        if lo > -1.0 or hi < -1.0:
            m = min(abs(1.0 + a), abs(1.0 + x))
            return math.factorial(n + 1) / m ** (n + 2)
        return None
    if fid == "inv1px2":
        m = 0.0 if (lo <= 0.0 <= hi) else min(abs(a), abs(x))
        return math.factorial(n + 1) / (m * m + 1.0) ** ((n + 2) / 2)
    raise ValueError(f"unknown function {fid!r}")


def evaluate(inputs, P):
    fid = P["fid"]
    a, n_raw = float(P["a"]), float(P["n"])
    x = float(inputs["x"])
    if fid not in FIDS:
        raise ValueError(f"unknown function {fid!r}")
    n = int(round(n_raw))
    if not 0 <= n <= N_MAX:
        raise ValueError(f"n must be in 0..{N_MAX}, got {n_raw}")
    if not (math.isfinite(a) and math.isfinite(x) and math.isfinite(n_raw)):
        raise ValueError("a, x and n must be finite")

    blank = {"in_domain": 0.0, "value": 0.0, "target": 0.0, "error": 0.0, "relative_error": 0.0,
             "derivative_gap": 0.0, "remainder_bound": 0.0, "bound_ok": 0.0, "next_term": 0.0,
             "radius": 0.0, "radius_finite": 0.0, "degree": float(n)}
    if not (domain_ok(fid, x) and domain_ok(fid, a)):
        return blank

    cs = coeffs(fid, a, n)
    value = poly_value(cs, a, x)
    target = fn_value(fid, x)
    error = abs(target - value)
    relative = error / abs(target) if abs(target) > 1e-12 else 0.0

    worst = 0.0
    for k, c in enumerate(cs):
        d = derivative_at(fid, a, k)
        worst = max(worst, abs(d - math.factorial(k) * c) / max(1.0, abs(d)))

    M = _bound_M(fid, a, x, n)
    bound = 0.0 if M is None else M * abs(x - a) ** (n + 1) / math.factorial(n + 1)

    scale = max([abs(c) * abs(x - a) ** k for k, c in enumerate(cs)] or [0.0])
    threshold = 1e-13 * max(1.0, scale)
    tail = coeffs(fid, a, min(n + 6, N_MAX + 6))
    next_term = 0.0
    for j in range(n + 1, len(tail)):
        term = abs(tail[j]) * abs(x - a) ** j
        if term > threshold:
            next_term = term
            break

    R = radius(fid, a)
    return {"in_domain": 1.0, "value": value, "target": target, "error": error,
            "relative_error": relative, "derivative_gap": worst, "remainder_bound": bound,
            "bound_ok": 1.0 if M is not None else 0.0, "next_term": next_term,
            "radius": 0.0 if R is None else R, "radius_finite": 0.0 if R is None else 1.0,
            "degree": float(n)}





CHECK_CASES = [
    {"name": "exp degree 4 at x=1", "inputs": {"x": 1.0},
     "params": {"fid": "exp", "a": 0.0, "n": 4.0},
     "expected": {"in_domain": 1.0, "value": 2.7083333333333335,
                  "target": 2.718281828459045, "error": 0.009948495125711903,
                  "relative_error": 0.0036598468273437122, "next_term": 0.008333333333333333,
                  "derivative_gap": 0.0, "radius_finite": 0.0},
     "atol": 1e-12, "rtol": 1e-12},
    {"name": "sin degree 3 at x=0.5", "inputs": {"x": 0.5},
     "params": {"fid": "sin", "a": 0.0, "n": 3.0},
     "expected": {"value": 0.4791666666666667, "target": 0.479425538604203,
                  "error": 0.0002588719375363336, "next_term": 0.00026041666666666666,
                  "radius_finite": 0.0},
     "atol": 1e-12, "rtol": 1e-12},
    {"name": "log degree 2 at x=0.5", "inputs": {"x": 0.5},
     "params": {"fid": "ln1p", "a": 0.0, "n": 2.0},
     "expected": {"value": 0.375, "target": 0.4054651081081644,
                  "error": 0.030465108108164382, "next_term": 0.041666666666666664,
                  "remainder_bound": 0.041666666666666664,
                  "bound_ok": 1.0, "radius": 1.0, "radius_finite": 1.0},
     "atol": 1e-12, "rtol": 1e-12},
    {"name": "geometric degree 3 at x=-0.5", "inputs": {"x": -0.5},
     "params": {"fid": "geom", "a": 0.0, "n": 3.0},
     "expected": {"value": 1.875, "target": 2.0, "error": 0.125,
                  "relative_error": 0.0625, "next_term": 0.0625,
                  "remainder_bound": 2.0, "radius": 1.0},
     "atol": 1e-12, "rtol": 1e-12},
    {"name": "complex poles degree 4 at x=0.5", "inputs": {"x": 0.5},
     "params": {"fid": "inv1px2", "a": 0.0, "n": 4.0},
     "expected": {"value": 0.8125, "target": 0.8, "error": 0.0125,
                  "next_term": 0.015625, "remainder_bound": 0.03125,
                  "radius": 1.0, "radius_finite": 1.0},
     "atol": 1e-12, "rtol": 1e-12},
    {"name": "square root centred at a=1", "inputs": {"x": 2.25},
     "params": {"fid": "sqrt1p", "a": 1.0, "n": 2.0},
     "expected": {"value": 1.7871019040144385, "target": 1.8027756377319946,
                  "error": 0.015673733717556176, "radius": 2.0},
     "atol": 1e-12, "rtol": 1e-12},
    {"name": "complex-pole recurrence at a=1.5", "inputs": {"x": 2.0},
     "params": {"fid": "inv1px2", "a": 1.5, "n": 2.0},
     "expected": {"value": 0.20755575785161584, "target": 0.2,
                  "error": 0.00755575785161584, "radius": 1.8027756377319946},
     "atol": 1e-12, "rtol": 1e-12},
    {"name": "small-angle approximation at ten degrees", "inputs": {"x": 0.17453292519943295},
     "params": {"fid": "sin", "a": 0.0, "n": 1.0},
     "expected": {"value": 0.17453292519943295, "target": 0.17364817766693033,
                  "error": 0.0008847475325026087,
                  "relative_error": 0.005095057975210186, "next_term": 0.000886096155701298},
     "atol": 1e-12, "rtol": 1e-12},
    {"name": "geometric at rightmost centre", "inputs": {"x": 3.0},
     "params": {"fid": "geom", "a": 2.5, "n": 2.0},
     "expected": {"value": 0.25072886297376096, "target": 0.25,
                  "error": 0.0007288629737609329, "radius": 3.5},
     "atol": 1e-12, "rtol": 1e-12},
    {"name": "log at leftmost centre", "inputs": {"x": -0.6},
     "params": {"fid": "ln1p", "a": -0.8, "n": 3.0},
     "expected": {"value": -0.776104579100767, "target": -0.9162907318741551,
                  "error": 0.14018615277338803, "radius": 0.2, "bound_ok": 1.0},
     "atol": 1e-12, "rtol": 1e-12},
    {"name": "exp at a negative centre", "inputs": {"x": -0.8},
     "params": {"fid": "exp", "a": -1.5, "n": 3.0},
     "expected": {"value": 0.44674376897718127, "target": 0.4493289641172216,
                  "error": 0.0025851951400403354, "radius_finite": 0.0},
     "atol": 1e-12, "rtol": 1e-12},
    {"name": "bound crossing a singularity", "inputs": {"x": -3.0},
     "params": {"fid": "geom", "a": 0.5, "n": 4.0},
     "expected": {"in_domain": 1.0, "bound_ok": 0.0, "remainder_bound": 0.0,
                  "value": 34.08230452674897, "target": -0.5, "error": 34.58230452674897},
     "atol": 1e-10, "rtol": 1e-12},
    {"name": "probe outside the log domain", "inputs": {"x": -1.5},
     "params": {"fid": "ln1p", "a": 0.0, "n": 4.0},
     "expected": {"in_domain": 0.0, "value": 0.0, "target": 0.0, "error": 0.0,
                  "derivative_gap": 0.0},
     "atol": 1e-12, "rtol": 1e-12},
    {"name": "constant polynomial at degree zero", "inputs": {"x": 2.0},
     "params": {"fid": "inv1px2", "a": 0.0, "n": 0.0},
     "expected": {"value": 1.0, "target": 0.2, "error": 0.8,
                  "derivative_gap": 0.0, "next_term": 4.0},
     "atol": 1e-12, "rtol": 1e-12},
    {"name": "exp degree 12 at a negative probe", "inputs": {"x": -2.0},
     "params": {"fid": "exp", "a": 0.0, "n": 12.0},
     "expected": {"value": 0.1353364331142109, "target": 0.1353352832366127,
                  "error": 1.1498775982000946e-06, "next_term": 1.3155568711124266e-06},
     "atol": 1e-12, "rtol": 1e-12},
]


# ---- topic-specific invariants, called by viz/check.py as extra_checks(report) ----

def _fd_weights(k, m=6):
    """Exact-rational Kth-derivative weights on 2m+1 nodes: sum(w*f(a+t)) = p^(k)(0)."""
    from fractions import Fraction
    n = 2 * m + 1
    nodes = [Fraction(j - m, 100) for j in range(n)]  # h = 0.01
    # Solve V^T w = rhs, V[i][j] = nodes[i]**j, rhs = k! e_k (Gauss-Jordan over Fractions).
    A = [[nodes[c] ** r for c in range(n)] + [Fraction(math.factorial(k)) if r == k else Fraction(0)]
         for r in range(n)]
    for col in range(n):
        piv = next(r for r in range(col, n) if A[r][col] != 0)
        A[col], A[piv] = A[piv], A[col]
        A[col] = [v / A[col][col] for v in A[col]]
        for r in range(n):
            if r != col and A[r][col] != 0:
                A[r] = [a - A[r][col] * b for a, b in zip(A[r], A[col])]
    return [float(x) for x in nodes], [float(A[r][n]) for r in range(n)]


def extra_checks(report) -> None:
    """Finite-difference coefficient check and a seeded Lagrange-remainder sweep."""
    import random
    grid = {"exp": (-2.5, 2.5), "sin": (-2.5, 2.5), "inv1px2": (-2.5, 2.5),
            "ln1p": (-0.8, 2.5), "sqrt1p": (-0.8, 2.5), "geom": (-0.8, 2.5)}
    weights = [_fd_weights(k) for k in range(5)]
    worst = 0.0
    for fid, (lo, hi) in grid.items():
        for i in range(7):
            a = lo + (hi - lo) * i / 6
            for n in range(5):
                for k, c in enumerate(coeffs(fid, a, n)):
                    nodes, w = weights[k]
                    fd = sum(wj * fn_value(fid, a + t) for wj, t in zip(w, nodes)) / math.factorial(k)
                    worst = max(worst, abs(fd - c) / max(1.0, abs(fd), abs(c)))
    tol = 1e-6
    report("OK" if worst < tol else "ERROR",
           f"Taylor coefficients vs 13-point finite differences (h=0.01, k<=4): max relative deviation {worst:.2e} (tolerance {tol:g})")

    rng = random.Random(20261010)
    checked = violations = 0
    for _ in range(240):
        fid = rng.choice(FIDS)
        lo, hi = grid[fid]
        a = rng.uniform(lo, hi)
        x = rng.uniform(-0.9, 4.0) if fid in ("ln1p", "sqrt1p") else rng.uniform(-4.0, 4.0)
        n = rng.randint(0, N_MAX)
        res = evaluate({"x": x}, {"fid": fid, "a": a, "n": n, "tau": 1e-2, "ymag": 1.0})
        if res["in_domain"] < 0.5 or res["bound_ok"] < 0.5:
            continue
        checked += 1
        if res["error"] > max(1e-9, res["remainder_bound"] * (1 + 1e-9)):
            violations += 1
    report("OK" if violations == 0 and checked > 100 else "ERROR",
           f"Lagrange remainder bound: {checked} seeded random cases, {violations} violations")
