"""Two-factor synthetic cohort with KNOWN theta (per-rider skill) and
delta (difficulty function). The sibling of synthetic.py: where that
generates single-curve cohorts, this generates cohorts with the latent
skill x difficulty structure M4 is designed to recover.

Riders sample across the FULL metric range so the rider x condition
incidence graph is connected (the M4 identification condition)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .latent_math import difficulty_u_shape, sigmoid


def make_latent_cohort(
    *,
    n_riders: int = 40,
    obs_per_rider: int = 20,
    metric_range: tuple[float, float] = (3.0, 35.0),
    a_true: float = 1.5,
    peak: float = 18.0,
    width: float = 8.0,
    floor: float = -1.0,
    seed: int = 42,
) -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(seed)
    thetas = rng.standard_normal(n_riders)  # true skills ~ N(0,1)

    def difficulty_fn(x: np.ndarray) -> np.ndarray:
        return difficulty_u_shape(x, peak=peak, width=width, floor=floor)

    rows = []
    theta_map: dict[str, float] = {}
    for i in range(n_riders):
        pseudo = f"rider-{i:03d}"
        theta_map[pseudo] = float(thetas[i])
        # spread each rider across the whole range -> connected graph
        xs = rng.uniform(metric_range[0], metric_range[1], obs_per_rider)
        probs = sigmoid(a_true * (thetas[i] - difficulty_fn(xs)))
        ys = (rng.uniform(size=obs_per_rider) < probs).astype(int)
        for x, y in zip(xs, ys):
            rows.append({"pseudonym": pseudo, "metric": float(x), "outcome": int(y)})

    df = pd.DataFrame(rows)
    truth = {
        "theta": theta_map,
        "a": a_true,
        "difficulty_fn": difficulty_fn,
        "peak": peak,
        "width": width,
        "floor": floor,
    }
    return df, truth
