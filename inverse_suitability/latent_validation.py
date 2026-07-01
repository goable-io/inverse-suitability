"""Validation gates for M4.

1. Backward-compat: integrating theta out of M4 must reproduce the single
   population curve (M4 ⊇ M3).
2. Promotion gate: M4 ships only if its skill-aware predictions beat the
   single curve on HELD-OUT per-rider observations (held-out Brier Skill
   Score > 0). If skill-conditioning doesn't earn its complexity, refuse.

See spec § 5."""

from __future__ import annotations

import numpy as np

from .fitters.latent_factor import fit_latent_factor
from .latent_math import sigmoid


def _population_logistic(metric: np.ndarray, outcome: np.ndarray, grid: np.ndarray):
    """Tiny single-curve baseline: logistic regression P(y|x) on a quadratic
    basis (no rider info). Returns a callable x -> prob. Deterministic."""
    X = np.column_stack([np.ones_like(metric), metric, metric ** 2])
    beta = np.zeros(3)
    for _ in range(200):  # Newton-Raphson IRLS
        eta = X @ beta
        p = np.clip(sigmoid(eta), 1e-6, 1 - 1e-6)
        W = p * (1 - p)
        grad = X.T @ (outcome - p)
        H = X.T @ (X * W[:, None]) + 1e-6 * np.eye(3)
        beta = beta + np.linalg.solve(H, grad)
    return lambda x: sigmoid(np.column_stack([np.ones_like(x), x, x ** 2]) @ beta)


def marginal_matches_single_curve(df, *, tol: float = 0.08, seed: int = 0) -> bool:
    metric = df["metric"].to_numpy(float)
    outcome = df["outcome"].to_numpy(float)
    fit = fit_latent_factor(df, seed=seed)
    grid = fit.grid
    m4_marg = fit.population_curve(grid)
    base = _population_logistic(metric, outcome, grid)(grid)
    return float(np.max(np.abs(m4_marg - base))) <= tol


def _split_per_rider(df, test_frac: float, seed: int):
    rng = np.random.default_rng(seed)
    test_mask = np.zeros(len(df), dtype=bool)
    for _, idx in df.groupby("pseudonym").indices.items():
        idx = np.array(idx)
        k = max(1, int(round(len(idx) * test_frac)))
        chosen = rng.choice(idx, size=k, replace=False)
        test_mask[chosen] = True
    return df[~test_mask], df[test_mask]


def _brier(probs: np.ndarray, outcome: np.ndarray) -> float:
    return float(np.mean((probs - outcome) ** 2))


def held_out_bss(df, *, test_frac: float = 0.3, seed: int = 0) -> float:
    train, test = _split_per_rider(df, test_frac, seed)
    fit = fit_latent_factor(train, seed=seed)
    base = _population_logistic(
        train["metric"].to_numpy(float), train["outcome"].to_numpy(float), fit.grid
    )

    y = test["outcome"].to_numpy(float)
    m4 = np.array(
        [
            fit.predict_prob(r, x) if r in fit.theta_mean else float(base(np.array([x]))[0])
            for r, x in zip(test["pseudonym"], test["metric"].to_numpy(float))
        ]
    )
    ref = base(test["metric"].to_numpy(float))
    brier_m4 = _brier(m4, y)
    brier_ref = _brier(ref, y)
    if brier_ref <= 0:
        return 0.0
    return 1.0 - brier_m4 / brier_ref


def passes_promotion_gate(df, *, seed: int = 0) -> bool:
    return held_out_bss(df, seed=seed) > 0.0
