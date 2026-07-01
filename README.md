# Inverse Suitability

**Identifying Condition Difficulty and Rider Skill from Behavioural Outcomes via Continuous-Item Response Theory**

[![reproduce](https://github.com/goable-io/inverse-suitability/actions/workflows/reproduce.yml/badge.svg)](https://github.com/goable-io/inverse-suitability/actions/workflows/reproduce.yml)

This repository is the **canonical implementation of the Inverse Suitability
method** — the continuous-item IRT calibration that Goable's production engine
depends on (the monorepo consumes this package as `inverse-suitability`) — together
with the **paper** (LaTeX + PDF) and a **self-contained, one-command
reproducibility package**. The method is public and reproducible; it is validated
here by **synthetic recovery only** — there is no real-rider data in this repo, and
none is needed to reproduce every number and figure in the paper.

Suitability scores for outdoor activities conflate two things: how hard a
condition intrinsically is, and how skilled the person facing it is. Inverse
Suitability is a continuous-item Item Response Theory model,
`P(y=1) = σ(a·(θ_r − δ(x,s)))`, that separates the two — recovering latent rider
skill `θ` and a latent, physics-anchored difficulty function `δ(x,s)` from binary
behavioural outcomes.

## Reproduce the results in one command

Requirements: [`uv`](https://docs.astral.sh/uv/) and (for the PDF)
[`tectonic`](https://tectonic-typesetting.github.io/).

```bash
# just the synthetic-recovery numbers:
uv run inverse-suitability latent-demo --out ./out

# or the full paper: regenerate table + figure from the fit, then build the PDF:
cd paper && make repro
```

`latent-demo` fits a synthetic cohort with **known** ground truth and reports how
well the model recovers it. Expected output (deterministic):

```json
{
  "theta_recovery_corr": 0.96,   // latent skill recovered at r = 0.96
  "difficulty_min_knots": 16.7,  // recovered difficulty min (ground truth: 18 kn)
  "discrimination_a": 2.16,      // recovered (ground truth: 2.0)
  "held_out_bss": 0.33,          // +0.33 Brier skill vs the single-curve baseline
  "marginal_matches": true,
  "identification_ok": true,
  "n_train": 2400
}
```

The GitHub Action in `.github/workflows/reproduce.yml` runs this on every push and
asserts the recovered values stay within the tolerances the paper claims.

## What's here

```
src/inverse_suitability/   the latent-factor (M4) method + synthetic data generator
  latent_math.py          link function + ground-truth difficulty
  synthetic_latent.py     synthetic two-factor cohort (known θ and δ)
  identification.py        rider×condition connectivity guard
  fitters/latent_factor.py MML-EM fit of σ(a·(θ − δ)) via Gauss–Hermite quadrature
  latent_validation.py     marginal-match + held-out Brier skill score
  latent_demo.py           end-to-end demo → stats.json
  cli.py                   `inverse-suitability latent-demo`
paper/                  LaTeX sources, compiled PDF, and reproducibility scripts
```

## What this is (and isn't)

This is the **canonical implementation** of the Inverse Suitability calibration —
Goable's production engine imports it directly as the single source of truth for
this method, so it is not a throwaway demo. What ships here is the *method* and a
**synthetic** data-generating process that exercises it end-to-end.

It does **not** contain: real behavioural-outcome data; the full production
calibration pipeline (the L3 ensemble fitters, IPW correction, drift monitoring
that wrap this method in the private engine); or any fitted difficulty atlas. The
method is public and reproducible; the data and the surrounding production system
are not. The paper makes no empirical claim on real riders — its validation is the
synthetic recovery study reproduced above.

## License

- **Code** (`src/inverse_suitability/`, `paper/reproducibility/`) — MIT (`LICENSE`).
- **Paper text** (`paper/` .tex, PDF, figures) — CC BY 4.0 (`paper/LICENSE`).

## Citation

```bibtex
@misc{carucci2026inversesuitability,
  author = {Carucci, Fabio},
  title  = {Inverse Suitability: Identifying Condition Difficulty and Rider Skill
            from Behavioural Outcomes via Continuous-Item Response Theory},
  year   = {2026},
  note   = {arXiv preprint (forthcoming)},
  url    = {https://github.com/goable-io/inverse-suitability}
}
```
