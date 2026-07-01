#!/usr/bin/env python3
"""Generate figures/difficulty-atlas.pdf from code -- never from the website SVG.

Two things in one figure, sharing the wind-speed axis (kitesurfing reference,
5--35 kn):

  * delta(x): the intrinsic difficulty function (a U-shape, minimised at the
    ground-truth optimum x* = 18 kn). This is what the "difficulty atlas"
    measures -- a property of the condition, not of who rides it.
  * three DERIVED suitability curves sigma(a*(theta - delta(x))) at skill levels
    theta in {-1, 0, +1} (beginner / intermediate / expert), a = 1.5. Skill
    shifts the suitability curve vertically without touching delta itself.

If the fitted model is available, the RECOVERED delta_hat(x) is overlaid so the
figure also shows recovery visually. The overlay is best-effort: if the fitter
internals are unavailable the figure still renders the ground-truth panel.

Run via the calibration package's environment (matplotlib is a dependency there):
    uv run --project <repo>/packages/calibration python gen_figure.py <out.pdf>
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from inverse_suitability.latent_math import difficulty_u_shape, sigmoid  # noqa: E402

# Ground-truth DGP parameters (mirror synthetic_latent.make_latent_cohort defaults).
PEAK_KN = 18.0
WIDTH = 8.0
FLOOR = -1.0
A_VIS = 1.5  # discrimination used for the illustrative derived curves
X_MIN, X_MAX = 5.0, 35.0

SKILL_LEVELS = [
    (-1.0, "beginner ($\\theta=-1$)", "#c87a50"),
    (0.0, "intermediate ($\\theta=0$)", "#1f6354"),
    (1.0, "expert ($\\theta=+1$)", "#7d4d8b"),
]
DELTA_COLOR = "#0f3d34"
FIT_COLOR = "#b0662f"


def _fitted_delta():
    """Best-effort recovered difficulty from the same synthetic cohort the demo
    fits. Returns (grid, delta_hat) or None if internals are unavailable."""
    try:
        from inverse_suitability.synthetic_latent import make_latent_cohort
        from inverse_suitability.fitters.latent_factor import fit_latent_factor

        df, _ = make_latent_cohort(
            n_riders=80, obs_per_rider=30, a_true=2.0, seed=11
        )
        fit = fit_latent_factor(df, seed=0)
        return np.asarray(fit.grid, dtype=float), np.asarray(fit.difficulty, dtype=float)
    except Exception as exc:  # pragma: no cover - overlay is optional
        print(f"[gen_figure] fitted overlay unavailable: {exc}", file=sys.stderr)
        return None


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("figures/difficulty-atlas.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)

    x = np.linspace(X_MIN, X_MAX, 400)
    delta = difficulty_u_shape(x, peak=PEAK_KN, width=WIDTH, floor=FLOOR)

    fig, (ax_s, ax_d) = plt.subplots(
        2, 1, figsize=(6.4, 5.4), sharex=True, height_ratios=[2.0, 1.3]
    )

    # --- top panel: derived skill-conditioned suitability curves ---
    for theta, label, color in SKILL_LEVELS:
        s = sigmoid(A_VIS * (theta - delta))
        ax_s.plot(x, s, color=color, lw=2.0, label=label)
    ax_s.axvline(PEAK_KN, color="0.55", lw=1.0, ls=(0, (2, 4)))
    ax_s.set_ylabel(r"suitability $\sigma(a(\theta-\delta(x)))$")
    ax_s.set_ylim(-0.02, 1.02)
    ax_s.legend(loc="lower center", frameon=False, fontsize=8, ncol=3)
    ax_s.set_title(
        "Skill shifts the suitability curve; the difficulty $\\delta$ underneath is invariant",
        fontsize=9.5,
    )

    # --- bottom panel: the intrinsic difficulty function delta(x) (the atlas) ---
    ax_d.plot(
        x, delta, color=DELTA_COLOR, lw=2.2, ls=(0, (6, 4)),
        label=r"$\delta(x)$ ground truth (min at $x^\star=18$ kn)",
    )
    fitted = _fitted_delta()
    if fitted is not None:
        gx, gd = fitted
        # centre the recovered difficulty on the ground-truth floor for visual
        # comparison (delta is identified up to the common theta-delta shift).
        gd = gd - float(np.min(gd)) + FLOOR
        ax_d.plot(gx, gd, color=FIT_COLOR, lw=1.8, marker="o", ms=2.5,
                  label=r"$\hat\delta(x)$ recovered (MML)")
    ax_d.axvline(PEAK_KN, color="0.55", lw=1.0, ls=(0, (2, 4)))
    ax_d.set_xlabel("wind speed (kn)")
    ax_d.set_ylabel(r"difficulty $\delta(x)$")
    ax_d.set_xlim(X_MIN, X_MAX)
    ax_d.legend(loc="upper center", frameon=False, fontsize=8)

    for ax in (ax_s, ax_d):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, color="0.9", lw=0.6)

    fig.tight_layout()
    fig.savefig(out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
