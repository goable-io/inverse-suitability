"""End-to-end L15 demo on a synthetic two-factor cohort with KNOWN theta/delta.

The sales + methodology artifact (mirrors L3's `demo --biased`): proves the
M4 reasoning machine recovers ground truth, emits stats.json a prospect or an
academic co-author can inspect. Runs in well under a minute, no real data."""

from __future__ import annotations

import json
import os

import numpy as np

from .synthetic_latent import make_latent_cohort
from .identification import check_identification
from .fitters.latent_factor import fit_latent_factor
from .latent_validation import marginal_matches_single_curve, held_out_bss


def run_latent_demo(out_dir: str, *, seed: int = 0) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    df, truth = make_latent_cohort(n_riders=80, obs_per_rider=30, a_true=2.0, seed=11)

    ident = check_identification(df)
    fit = fit_latent_factor(df, seed=seed)

    riders = list(truth["theta"].keys())
    true_theta = np.array([truth["theta"][r] for r in riders])
    est_theta = np.array([fit.theta_mean[r] for r in riders])
    corr = float(np.corrcoef(true_theta, est_theta)[0, 1])

    stats = {
        "theta_recovery_corr": corr,
        "difficulty_min_knots": float(fit.grid[fit.difficulty.argmin()]),
        "discrimination_a": float(fit.a),
        "marginal_matches": bool(marginal_matches_single_curve(df, seed=seed)),
        "held_out_bss": float(held_out_bss(df, seed=seed)),
        "identification_ok": bool(ident.ok),
        "n_train": int(len(df)),
    }
    with open(os.path.join(out_dir, "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)
    return stats
