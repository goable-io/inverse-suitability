"""Pure math primitives for the M4 latent-factor (IRT) calibration method.

The model: P(y=1 | rider r, condition x) = sigmoid(a * (theta_r - delta(x)))
  theta_r   latent skill of the rider (one scalar per pseudonym)
  delta(x)  latent difficulty of the condition (a smooth function of the metric)
  a         discrimination (scalar in Phase 1)

See spec docs/superpowers/specs/2026-06-23-engine-l15-inverse-suitability-design.md.
"""

from __future__ import annotations

import numpy as np


def sigmoid(z: np.ndarray) -> np.ndarray:
    """Numerically stable logistic. Avoids overflow for large |z|."""
    z = np.asarray(z, dtype=float)
    out = np.empty_like(z)
    pos = z >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    out[~pos] = ez / (1.0 + ez)
    return out


def difficulty_u_shape(
    x: np.ndarray, peak: float = 18.0, width: float = 8.0, floor: float = -1.0
) -> np.ndarray:
    """Ground-truth difficulty delta(x): a parabola in difficulty space,
    minimum `floor` at `peak`. Higher away from the peak = harder. Feeding
    this through sigmoid(a*(theta - delta)) yields a single-peaked
    suitability curve (easy near the sweet spot, hard at the extremes)."""
    x = np.asarray(x, dtype=float)
    return ((x - peak) / width) ** 2 + floor
