#!/usr/bin/env python3
"""Generate the three original figures referenced by the guide."""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import model as M

OUT = Path(__file__).resolve().parent / "figures"
# Tokens from assets/draft.css :root — check.py rejects any other colour here.
PAPER, INK, ACCENT, ACCENT_INK, FOG = "#ECEAE3", "#1B1B19", "#D4572A", "#B4441C", "#8FA8BF"
MONO = "DejaVu Sans Mono"
LINES = {"solid": "-", "dash": (0, (5, 4)), "dot": (0, (.6, 3.2)), "chain": (0, (10, 3, 2, 3))}
NUMBERS = {}

plt.rcParams.update({
    "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER,
    "text.color": INK, "axes.labelcolor": INK, "axes.edgecolor": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": .9,
    "xtick.direction": "out", "ytick.direction": "out", "axes.grid": False,
    "lines.color": INK, "lines.linewidth": 1.8, "axes.prop_cycle": plt.cycler(color=[INK]),
    "font.size": 9.5,
    "axes.titlesize": 10, "axes.titleweight": "bold", "axes.titlelocation": "left",
})
plt.rcParams["font.family"] = "DejaVu Sans"


def save(fig, name, numbers):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=180, bbox_inches="tight")
    plt.close(fig)
    NUMBERS[name] = {key: float(value) for key, value in numbers.items()}
    print(f"wrote {OUT / name}")


def tag(ax, letter, title):
    ax.set_title(title, x=0.035, pad=10)
    ax.text(0, 1.035, letter, transform=ax.transAxes, fontsize=8, fontweight="bold", family="DejaVu Sans Mono",
            va="bottom", bbox=dict(boxstyle="square,pad=.25", fc=PAPER, ec=INK, lw=.8))


def dim(ax, x1, x2, y, label):
    ax.annotate("", (x1, y), (x2, y), arrowprops=dict(arrowstyle="<|-|>", lw=.7, color=INK, mutation_scale=7, shrinkA=0, shrinkB=0))
    ax.text((x1 + x2) / 2, y, label, ha="center", va="bottom", fontsize=8.5, family="DejaVu Sans Mono")


def endlabel(ax, x, y, text, dx=6, dy=0):
    ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=9, style="italic", va="center")


def valid_interval(xs, err, tau):
    """Interpolate the tolerance interval around zero; flag clipped endpoints."""
    inside = err <= tau
    centre = int(np.argmin(np.abs(xs)))
    if not inside[centre]:
        return None
    i = centre
    while i > 0 and inside[i - 1]:
        i -= 1
    j = centre
    while j < len(xs) - 1 and inside[j + 1]:
        j += 1
    lo = xs[0] if i == 0 else xs[i] + (xs[i - 1] - xs[i]) * (tau - err[i]) / (err[i - 1] - err[i])
    hi = xs[-1] if j == len(xs) - 1 else xs[j] + (xs[j + 1] - xs[j]) * (tau - err[j]) / (err[j + 1] - err[j])
    return float(lo), float(hi), bool(i == 0 or j == len(xs) - 1)


def main():

    a, tau = 0.0, 1e-2
    xs = np.linspace(-2.4, 2.4, 4801)
    target = np.array([M.fn_value("exp", float(x)) for x in xs])
    fig, ax = plt.subplots(figsize=(8, 4.0))
    tag(ax, "A", "e^x and P1, P4, P8: intervals within |R| <= 1e-2 (blue bars)")
    bars = {}
    for degree, style, y_bar in ((8, LINES["chain"], -1.50), (4, LINES["dash"], -1.05), (1, LINES["dot"], -0.60)):
        cs = M.coeffs("exp", a, degree)
        poly = np.array([M.poly_value(cs, a, float(x)) for x in xs])
        interval = valid_interval(xs, np.abs(target - poly), tau)
        bars[degree] = interval
        ax.plot(xs, poly, color=INK, lw=1.2, ls=style)
        if interval:
            lo, hi, clipped = interval
            ax.plot([lo, hi], [y_bar, y_bar], color=FOG, lw=8, solid_capstyle="butt", zorder=0)
            for edge in (lo, hi):
                ax.plot([edge, edge], [y_bar - .13, y_bar + .13], color=INK, lw=.7)
            ax.text(-2.40, y_bar, f"P{degree}", va="center", ha="left", fontsize=9, family=MONO)
            inside = hi > 1.9
            label = f"dx = {hi - lo:.2f}" + ("+ (edge)" if clipped else "")
            ax.text(hi - .08 if inside else hi + .08, y_bar, label, va="center", ha="right" if inside else "left",
                    fontsize=8.5, family=MONO, bbox=dict(fc=PAPER, ec="none", pad=1.2))
    ax.plot(xs, target, "-", color=INK, lw=2.2)
    ax.plot([a], [1.0], "o", color=ACCENT, ms=5.5)
    ax.plot([1.0], [np.e], "o", color=ACCENT, ms=5.5, mfc=PAPER)
    ax.annotate(f"x = 1: |R4| = {abs(np.e - float(M.poly_value(M.coeffs('exp', a, 4), a, 1.0))):.4f}",
                (1.0, np.e), xytext=(-6, 30), textcoords="offset points", color=ACCENT_INK, fontsize=8.5,
                arrowprops=dict(arrowstyle="-", lw=.7, color=ACCENT, connectionstyle="angle,angleA=0,angleB=80"))
    endlabel(ax, xs[-1], target[-1], "f = e^x")
    ax.set(xlabel="x", ylabel="y", xlim=(-2.45, 2.85), ylim=(-2.05, 10.4))
    save(fig, "01-local-fit.png",
         {"tau": tau, "width_p1": bars[1][1] - bars[1][0], "width_p4": bars[4][1] - bars[4][0],
          "width_p8": bars[8][1] - bars[8][0], "width_p8_clipped": 1.0 if bars[8][2] else 0.0,
          "probe_error_n4": abs(np.e - float(M.poly_value(M.coeffs("exp", a, 4), a, 1.0)))})

    fig, ax = plt.subplots(figsize=(8, 3.9))
    tag(ax, "B", "ln(1+x) at a = 0: error by degree (R = 1)")
    degrees = np.arange(0, 13)
    series = ((0.5, LINES["dot"], "x = 0.5 (inside radius)"), (1.0, LINES["chain"], "x = 1.0 (boundary)"),
              (1.5, LINES["dash"], "x = 1.5 (outside radius)"))
    numbers = {}
    for probe, style, label in series:
        err = np.array([abs(float(M.fn_value("ln1p", probe)) - float(M.poly_value(M.coeffs("ln1p", 0.0, int(n)), 0.0, probe)))
                        for n in degrees])
        err = np.maximum(err, 1e-16)
        ax.semilogy(degrees, err, color=INK, lw=1.6, ls=style, marker="o", ms=3)
        endlabel(ax, 12, err[-1], label, dx=-4, dy=8)
        numbers[f"err_n12_x{str(probe).replace('.', '')}"] = float(err[-1])
    ax.axhline(1e-2, color=INK, lw=.8, ls=LINES["dot"])
    ax.text(0.15, 1.3e-2, "τ = 1e-2", fontsize=8.5, family=MONO)
    ax.axvline(0, color=INK, lw=.5)
    ax.set(xlabel="degree n", ylabel="|f(x) - Pn(x)|", xlim=(-0.4, 15.4), ylim=(1e-13, 3e1))
    ax.set_yticks([1e-12, 1e-9, 1e-6, 1e-3, 1e0])
    ax.set_yticklabels(["1e-12", "1e-9", "1e-6", "1e-3", "1"])
    save(fig, "02-error-vs-degree.png", dict(radius=1.0, **numbers))


    deg = np.linspace(0, 30, 601)
    theta = np.radians(deg)
    exact, linear = np.sin(theta), theta
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.4, 4.8), sharex=True, gridspec_kw=dict(hspace=.12, height_ratios=[1.25, 1]))
    tag(ax1, "C", "sin(theta) and theta: small-angle approximation")
    ax1.plot(deg, linear, color=INK, lw=1.4, ls=LINES["dash"])
    ax1.plot(deg, exact, "-", color=INK, lw=2.2)
    ax1.annotate("θ", (26, np.radians(26)), xytext=(4, 4), textcoords="offset points", style="italic")
    ax1.annotate("sinθ", (26, np.sin(np.radians(26))), xytext=(4, -10), textcoords="offset points", style="italic")
    ax1.set(ylabel="radians", xlim=(0, 30), ylim=(0, 0.58))

    rel = np.array([M.evaluate({"x": float(t)}, {"fid": "sin", "a": 0.0, "n": 1})["relative_error"]
                    for t in theta]) * 100
    readouts = {}
    for degrees_value in (10.0, 20.0, 30.0):
        readouts[degrees_value] = M.evaluate({"x": float(np.radians(degrees_value))},
                                             {"fid": "sin", "a": 0.0, "n": 1})["relative_error"] * 100
    ax2.plot(deg, rel, "-", color=INK, lw=1.8)
    ax2.axvspan(0, 10, color=FOG, alpha=.30, lw=0)
    ax2.plot([10], [readouts[10.0]], "o", color=ACCENT, ms=6)
    ax2.annotate(f"10°: {readouts[10.0]:.2f}%", (10, readouts[10.0]), xytext=(10, 12),
                 textcoords="offset points", color=ACCENT_INK, fontsize=8.5,
                 arrowprops=dict(arrowstyle="-", lw=.7, color=ACCENT))
    ax2.set(xlabel="angle / degrees", ylabel="relative error / %", ylim=(0, 4.2))
    save(fig, "03-small-angle.png",
         {"rel_10deg": readouts[10.0], "rel_20deg": readouts[20.0], "rel_30deg": readouts[30.0],
          "theta_10deg_rad": float(np.radians(10))})

    (OUT / "figures.json").write_text(json.dumps(NUMBERS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT / 'figures.json'}")


if __name__ == "__main__":
    main()
