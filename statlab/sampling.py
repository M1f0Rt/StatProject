"""Sampling from a finite population: with/without replacement and stratified."""
from __future__ import annotations

import numpy as np
import pandas as pd


def proportional_allocation(strata: pd.Series, n: int) -> pd.Series:
    """n_h proportional to N_h (largest-remainder rounding, at least 1 per stratum)."""
    N_h = strata.value_counts().sort_index()
    raw = n * N_h / N_h.sum()
    n_h = np.floor(raw).astype(int).clip(lower=1)
    rest = n - n_h.sum()
    for h in (raw - np.floor(raw)).sort_values(ascending=False).index[:max(rest, 0)]:
        n_h[h] += 1
    return n_h


def draw(n: int, N: int, scheme: str, rng, strata=None, n_h=None) -> np.ndarray:
    """Indices of one sample. scheme: 'wr', 'wor' or 'strat' (proportional, without replacement)."""
    if scheme == "wr":
        return rng.integers(0, N, n)
    if scheme == "wor":
        return rng.choice(N, n, replace=False)
    if scheme == "strat":
        idx = [rng.choice(np.flatnonzero(strata == h), k, replace=False) for h, k in n_h.items()]
        return np.concatenate(idx)
    raise ValueError(scheme)


def simulate(values, n: int, estimators: dict, scheme: str, M: int = 2000,
             strata=None, seed: int = 0) -> pd.DataFrame:
    """Repeat sampling M times; returns an M x len(estimators) table of estimates.

    For proportional allocation the sample is self-weighting, so the plain
    estimators apply to the pooled stratified sample.
    """
    v = np.asarray(values, float)
    rng = np.random.default_rng(seed)
    strata = None if strata is None else np.asarray(strata)
    n_h = proportional_allocation(pd.Series(strata), n) if scheme == "strat" else None
    rows = []
    for _ in range(M):
        x = v[draw(n, len(v), scheme, rng, strata, n_h)]
        rows.append({k: f(x) for k, f in estimators.items()})
    return pd.DataFrame(rows)


def theoretical_se_mean(values, n: int, scheme: str, strata=None) -> float:
    """Standard error of the sample mean under each design (Cochran, ch. 2, 5)."""
    v = np.asarray(values, float)
    N = len(v)
    sigma2 = v.var(ddof=0)
    if scheme == "wr":
        return np.sqrt(sigma2 / n)
    if scheme == "wor":
        return np.sqrt(sigma2 / n * (N - n) / (N - 1))
    if scheme == "strat":
        s = pd.Series(v).groupby(np.asarray(strata))
        N_h, S2_h = s.size(), s.var(ddof=1)
        n_h = proportional_allocation(pd.Series(np.asarray(strata)), n)
        W_h = N_h / N
        return np.sqrt((W_h ** 2 * (1 - n_h / N_h) * S2_h / n_h).sum())
    raise ValueError(scheme)


def consistency_curve(values, estimators: dict, ns, M: int = 1000, seed: int = 0) -> pd.DataFrame:
    """Sampling distribution of each estimator as n grows (i.i.d. draws from the population).

    Returns long table: n, estimator, mean, q05, q95, rmse (vs the population value).
    """
    v = np.asarray(values, float)
    rng = np.random.default_rng(seed)
    truth = {k: f(v) for k, f in estimators.items()}
    rows = []
    for n in ns:
        idx = rng.integers(0, len(v), size=(M, n))
        samples = v[idx]
        for k, f in estimators.items():
            est = np.array([f(s) for s in samples])
            rows.append(dict(n=n, estimator=k, truth=truth[k], mean=est.mean(),
                             q05=np.percentile(est, 5), q95=np.percentile(est, 95),
                             rmse=np.sqrt(((est - truth[k]) ** 2).mean()),
                             p_far=(np.abs(est - truth[k]) > 0.1 * max(abs(truth[k]), 1e-12)).mean()))
    return pd.DataFrame(rows)
