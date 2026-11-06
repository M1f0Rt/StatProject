"""One plotting style for the whole notebook."""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats as ss

# Categorical slots in fixed order (validated CVD-safe palette)
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
METHOD_COLOR = {"r2SCAN": C[0], "NN-r2SCAN": C[1]}
DT_COLOR = dict(zip(["BH", "TC", "ISO", "INC", "NC"], C[:5]))
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def setup():
    plt.rcParams.update({
        "figure.figsize": (8, 4.2),
        "figure.dpi": 110,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": INK2,
        "axes.labelcolor": INK,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "lines.linewidth": 2,
        "font.size": 10,
    })


def hist_with_fits(ax, x, fits: dict, bins=80, xlim=None, color=C[0], label="data"):
    """Density histogram plus fitted pdfs. fits: {name: (scipy_dist_name, params)}."""
    x = np.asarray(x, float)
    rng = xlim or (np.percentile(x, 0.5), np.percentile(x, 99.5))
    ax.hist(x, bins=bins, range=rng, density=True, color=color, alpha=0.35,
            edgecolor="white", linewidth=0.5, label=label)
    grid = np.linspace(*rng, 600)
    styles = ["-", "--", ":", "-."]
    for i, (name, (dist, p)) in enumerate(fits.items()):
        ax.plot(grid, getattr(ss, dist).pdf(grid, *p), color=INK if i == 0 else INK2,
                ls=styles[i % 4], lw=1.6, label=name)
    ax.set_xlim(rng)
    ax.set_ylabel("плотность")
    ax.legend()


def qq(ax, x, dist="norm", params=None, color=C[0], label=None):
    """QQ-plot against a (fitted) distribution."""
    x = np.sort(np.asarray(x, float))
    d = getattr(ss, dist)
    params = params if params is not None else d.fit(x)
    p = (np.arange(1, len(x) + 1) - 0.5) / len(x)
    q = d.ppf(p, *params)
    ax.plot(q, x, "o", ms=3, color=color, alpha=0.6, label=label)
    lo, hi = np.percentile(q, [0.5, 99.5])
    ax.plot([lo, hi], [lo, hi], color=INK2, lw=1, ls="--")
    ax.set_xlabel(f"теоретические квантили ({dist})")
    ax.set_ylabel("выборочные квантили")


def survival_loglog(ax, x, color=C[0], label=None):
    """Empirical P(|X| > t) on log-log axes: a straight tail means a power law."""
    a = np.sort(np.abs(np.asarray(x, float)))
    a = a[a > 0]
    s = 1 - np.arange(1, len(a) + 1) / (len(a) + 1)
    ax.loglog(a, s, color=color, lw=2, label=label)
    ax.set_ylabel(r"$P(|X|>t)$")


def consistency_panel(ax, cc, estimator, color=C[0], label=None):
    """Mean and 90 % band of an estimator vs n, with the population value."""
    d = cc[cc.estimator == estimator]
    ax.fill_between(d.n, d.q05, d.q95, color=color, alpha=0.2, lw=0)
    ax.plot(d.n, d["mean"], color=color, label=label or estimator)
    ax.axhline(d.truth.iloc[0], color=INK2, ls="--", lw=1)
    ax.set_xscale("log")
    ax.set_xlabel("объём выборки $n$")
