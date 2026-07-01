"""Inverse Suitability -- continuous-item IRT calibration (canonical implementation).

This package is the single source of truth for the Inverse Suitability method:
the latent-factor calibration that identifies condition difficulty ``delta(x,s)``
and rider skill ``theta_r`` from behavioural outcomes,
``P(y=1) = sigmoid(a * (theta_r - delta(x,s)))``. Goable's production engine
depends on this package directly; it also backs the paper "Inverse Suitability:
Identifying Condition Difficulty and Rider Skill from Behavioural Outcomes via
Continuous-Item Response Theory."

What ships here is the *method* plus a synthetic data-generating process with known
ground truth. It does NOT include real data, the full production pipeline (L3
ensemble, IPW, drift monitoring), or any fitted difficulty atlas -- those live in
Goable's private engine.

Entry point: the ``inverse-suitability latent-demo`` command (see ``cli``).
"""

__version__ = "0.1.0"
