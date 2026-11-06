"""Descriptive statistics, distribution fitting and the less common tests."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy import stats as ss


def describe(x, name: str | None = None) -> pd.Series:
    """Moments and robust statistics of a sample."""
    x = np.asarray(x, float)
    q1, med, q3 = np.percentile(x, [25, 50, 75])
    return pd.Series({
        "n": len(x),
        "mean": x.mean(),
        "std": x.std(ddof=1),
        "median": med,
        "IQR": q3 - q1,
        "MAD": ss.median_abs_deviation(x),
        "MAE": np.abs(x).mean(),
        "RMSE": np.sqrt((x ** 2).mean()),
        "min": x.min(),
        "max": x.max(),
        "skew": ss.skew(x),
        "ex.kurt": ss.kurtosis(x),
    }, name=name)


def error_metrics(e) -> pd.Series:
    """Accuracy metrics of signed errors e = calc - ref."""
    e = np.asarray(e, float)
    a = np.abs(e)
    return pd.Series({
        "MAE": a.mean(),
        "RMSE": np.sqrt((e ** 2).mean()),
        "MSE (bias)": e.mean(),
        "SD": e.std(ddof=1),
        "MedAE": np.median(a),
        "Q95|e|": np.percentile(a, 95),
        "MaxAE": a.max(),
    })


DEFAULT_DISTS = ("norm", "laplace", "logistic", "t", "cauchy", "johnsonsu")


def fit_distributions(x, dists=DEFAULT_DISTS) -> pd.DataFrame:
    """MLE fit of each candidate; AIC, BIC and the (naive) KS p-value.

    The KS p-value is optimistic because the parameters were estimated on the
    same sample; use ks_parametric_bootstrap for the final candidate.
    """
    x = np.asarray(x, float)
    n = len(x)
    rows = []
    for name in dists:
        d = getattr(ss, name)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p = d.fit(x)
        ll = d.logpdf(x, *p).sum()
        k = len(p)
        rows.append(dict(
            dist=name, k=k, logL=ll,
            AIC=2 * k - 2 * ll, BIC=k * np.log(n) - 2 * ll,
            KS_D=ss.kstest(x, d.cdf, args=p).statistic,
            KS_p_naive=ss.kstest(x, d.cdf, args=p).pvalue,
            params=np.round(p, 4),
        ))
    out = pd.DataFrame(rows).sort_values("AIC").reset_index(drop=True)
    out["dAIC"] = out.AIC - out.AIC.min()
    return out


def ks_parametric_bootstrap(x, dist: str, B: int = 500, seed: int = 0):
    """Lilliefors-type KS test with estimated parameters.

    The null distribution of D is simulated: draw n points from the fitted
    model, refit, recompute D. Returns (D, p, fitted params).
    """
    x = np.asarray(x, float)
    d = getattr(ss, dist)
    rng = np.random.default_rng(seed)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        p = d.fit(x)
        D = ss.kstest(x, d.cdf, args=p).statistic
        Ds = np.empty(B)
        for b in range(B):
            y = d.rvs(*p, size=len(x), random_state=rng)
            pb = d.fit(y)
            Ds[b] = ss.kstest(y, d.cdf, args=pb).statistic
    return D, (1 + (Ds >= D).sum()) / (B + 1), p


def pitman_morgan(x, y):
    """Test H0: Var(X) = Var(Y) for *paired* samples.

    Var X - Var Y = Cov(X+Y, X-Y), so H0 is equivalent to zero correlation
    between U = X+Y and V = X-Y; r_UV is tested with a t statistic, n-2 df.
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    r = np.corrcoef(x + y, x - y)[0, 1]
    t = r * np.sqrt((n - 2) / (1 - r ** 2))
    p = 2 * ss.t.sf(abs(t), n - 2)
    return dict(var_x=x.var(ddof=1), var_y=y.var(ddof=1), ratio=x.var(ddof=1) / y.var(ddof=1),
                r_uv=r, t=t, p=p)


def icc_oneway(values, groups):
    """Intraclass correlation from one-way random-effects ANOVA (unequal sizes).

    ICC is the share of variance explained by belonging to the same group:
    0 means groups do not matter, 1 means members of a group are identical.
    """
    df = pd.DataFrame({"v": values, "g": groups})
    N, g = len(df), df.g.nunique()
    grp = df.groupby("g", observed=True).v
    n_i, m_i = grp.size(), grp.mean()
    msb = (n_i * (m_i - df.v.mean()) ** 2).sum() / (g - 1)
    msw = ((df.v - grp.transform("mean")) ** 2).sum() / (N - g)
    k0 = (N - (n_i ** 2).sum() / N) / (g - 1)
    icc = (msb - msw) / (msb + (k0 - 1) * msw)
    F = msb / msw
    return dict(ICC=icc, F=F, p=ss.f.sf(F, g - 1, N - g), k0=k0)


def hill_estimator(x, ks):
    """Hill estimate of the tail index alpha of |x| for each number k of top order stats.

    P(|X| > t) ~ t^-alpha; alpha < 1 means the mean does not exist,
    alpha < 2 means infinite variance.
    """
    a = np.sort(np.abs(np.asarray(x, float)))[::-1]
    out = []
    for k in ks:
        xi = np.mean(np.log(a[:k] / a[k]))
        out.append(1 / xi)
    return np.array(out)


def rank_biserial(x):
    """Matched-pairs rank-biserial correlation (effect size for Wilcoxon)."""
    x = np.asarray(x, float)
    x = x[x != 0]
    r = ss.rankdata(np.abs(x))
    return (r[x > 0].sum() - r[x < 0].sum()) / r.sum()


def sign_flip_test(d, stat=np.mean, B: int = 20000, seed: int = 0):
    """Paired permutation test: under H0 (d symmetric about 0) signs are exchangeable."""
    d = np.asarray(d, float)
    rng = np.random.default_rng(seed)
    obs = stat(d)
    flipped = rng.choice([-1.0, 1.0], size=(B, len(d))) * d
    null = flipped.mean(1) if stat is np.mean else np.array([stat(row) for row in flipped])
    return obs, (1 + (np.abs(null) >= abs(obs)).sum()) / (B + 1)


def holm(pvals):
    """Holm-Bonferroni adjusted p-values."""
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    run = 0.0
    for i, j in enumerate(order):
        run = max(run, (m - i) * p[j])
        adj[j] = min(1.0, run)
    return adj


def bootstrap_ci(values, stat=np.mean, groups=None, B: int = 5000, level=0.95, seed: int = 0):
    """Percentile bootstrap CI; with groups, whole groups (clusters) are resampled."""
    v = np.asarray(values, float)
    rng = np.random.default_rng(seed)
    if groups is None:
        idx = rng.integers(0, len(v), size=(B, len(v)))
        boot = np.array([stat(v[i]) for i in idx])
    else:
        g = pd.Series(v).groupby(np.asarray(groups)).apply(np.asarray).tolist()
        boot = np.empty(B)
        for b in range(B):
            pick = rng.integers(0, len(g), len(g))
            boot[b] = stat(np.concatenate([g[i] for i in pick]))
    lo, hi = np.percentile(boot, [(1 - level) / 2 * 100, (1 + level) / 2 * 100])
    return stat(v), lo, hi


def cv_r2(X, y, k: int = 5, seed: int = 0) -> float:
    """Out-of-fold R^2 of ordinary least squares (with intercept), k-fold CV."""
    X = np.column_stack([np.ones(len(y)), np.asarray(X, float)])
    y = np.asarray(y, float)
    fold = np.random.default_rng(seed).permutation(len(y)) % k
    pred = np.empty_like(y)
    for f in range(k):
        tr, te = fold != f, fold == f
        b, *_ = np.linalg.lstsq(X[tr], y[tr], rcond=None)
        pred[te] = X[te] @ b
    return 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
