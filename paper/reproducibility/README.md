# Reproducibility

Every data-derived artifact in the paper is generated from the code in this
repository, not hand-typed. This directory holds the scripts that do it.

## What is generated (never edited by hand)

| Artifact | Produced by | Consumed by |
|---|---|---|
| `out/stats.json` | `inverse-suitability latent-demo` | the two scripts below |
| `../sections/results.tex` | `gen_results_tex.py` | `05-synthetic-recovery.tex` via `\input` |
| `../figures/difficulty-atlas.pdf` | `gen_figure.py` | `06-atlas.tex` via `\includegraphics` |

`results.tex` contains the results table **and** the `\newcommand` macros
(`\thetaRecoveryCorr`, `\difficultyMinKnots`, `\heldOutBSS`, `\nTrain`,
`\discriminationA`) that the prose cites, so the numbers in the text and the table
share a single source: the JSON.

## One command

From the `paper/` directory:

```bash
make repro
```

This runs `reproducibility/run.sh` and then rebuilds `main.pdf`. `run.sh`:

1. runs `uv run inverse-suitability latent-demo --out reproducibility/out --seed 0`
   against the `inverse-suitability` package at the repo root;
2. renders `sections/results.tex` from `out/stats.json`;
3. renders `figures/difficulty-atlas.pdf` from the package's difficulty and link
   functions.

To run just the data step without rebuilding the PDF:

```bash
bash reproducibility/run.sh
```

## Requirements

- [`uv`](https://docs.astral.sh/uv/) on `PATH` (runs the `inverse-suitability`
  package in its own environment; `numpy`, `scipy`, `matplotlib` are declared in
  the repo-root `pyproject.toml`).
- [`tectonic`](https://tectonic-typesetting.github.io/) for the LaTeX build
  (`make`).

No network access and no proprietary data are needed. The run is deterministic
(fixed cohort seed `11` inside `make_latent_cohort`; fit `--seed 0`) and completes
in well under a minute.

## Provenance and the ground-truth / recovered distinction

The reference cohort is
`make_latent_cohort(n_riders=80, obs_per_rider=30, a_true=2.0, seed=11)`. Its
**ground-truth** difficulty is minimised at `x* = 18 kn` with true discrimination
`a_true = 2.0` — these are inputs to the *generator* and are stated as fixed prose
in the paper (Section 5 and the Appendix). The **recovered** values written into
`results.tex` (e.g. `difficulty_min_knots ≈ 16.7`) are what the estimator infers
from outcomes alone. The two are deliberately kept separate: the prose declares
truth, the generated table reports recovery. Do not edit `results.tex` to swap
them; regenerate it instead.

## arXiv submission notes

- Primary category `stat.AP`; cross-list `stat.ME` and `physics.ao-ph`.
- A first submission to `stat.*` typically needs an endorsement — resolved by a
  co-author or a found endorser (logistics, not part of the build).
- The author block has a `% co-author placeholder` line in `main.tex`.
