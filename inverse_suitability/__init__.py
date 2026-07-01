"""Inverse Suitability -- synthetic-recovery reproducibility package.

This is the slim, public subset of Goable's calibration engine that reproduces
the results in the paper "Inverse Suitability: Identifying Condition Difficulty
and Rider Skill from Behavioural Outcomes via Continuous-Item Response Theory."

It contains ONLY the latent-factor (M4) method and its synthetic data-generating
process -- no proprietary L3 ensemble, no real data. Everything here runs on
synthetic cohorts with known ground truth.

Entry point: the ``inverse-suitability latent-demo`` command (see ``cli``).
"""

__version__ = "0.1.0"
