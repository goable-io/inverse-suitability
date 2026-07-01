#!/usr/bin/env bash
# Regenerate every DATA-DERIVED artifact in the paper from the calibration code.
#
# The paper's results table and figure are NOT hand-authored: they are produced
# here by running the exact same `latent-demo` command a reviewer would run, then
# rendering its stats.json into LaTeX + a PDF figure. Run `make repro` (which
# calls this) whenever the model changes; the numbers cannot drift.
#
# Requires: `uv` on PATH, and the inverse-suitability Python package (this repo root).  No
# network, no proprietary data, <60s.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAPER_DIR="$(cd "$HERE/.." && pwd)"
# Standalone repo layout: paper/ sits under the repo root, and the
# inverse-suitability package (pyproject.toml) IS the repo root.
REPO_ROOT="$(cd "$PAPER_DIR/.." && pwd)"
CALIB="$REPO_ROOT"

OUT="$HERE/out"
STATS="$OUT/stats.json"
RESULTS_TEX="$PAPER_DIR/sections/results.tex"
FIGURE_PDF="$PAPER_DIR/figures/difficulty-atlas.pdf"
SEED="${SEED:-0}"

if ! command -v uv >/dev/null 2>&1; then
  echo "error: 'uv' not found on PATH (needed to run inverse-suitability)." >&2
  exit 1
fi
if [ ! -d "$CALIB" ]; then
  echo "error: calibration package not found at $CALIB" >&2
  exit 1
fi

mkdir -p "$OUT"

echo ">> [1/3] running inverse-suitability latent-demo (seed=$SEED) ..."
uv run --project "$CALIB" inverse-suitability latent-demo --out "$OUT" --seed "$SEED"

echo ">> [2/3] rendering results.tex from stats.json ..."
uv run --project "$CALIB" python "$HERE/gen_results_tex.py" "$STATS" "$RESULTS_TEX"

echo ">> [3/3] rendering difficulty-atlas.pdf ..."
uv run --project "$CALIB" python "$HERE/gen_figure.py" "$FIGURE_PDF"

echo ""
echo "done. regenerated:"
echo "  - $STATS"
echo "  - $RESULTS_TEX   (LaTeX macros + results table)"
echo "  - $FIGURE_PDF"
echo ""
echo "cohort provenance: make_latent_cohort(n_riders=80, obs_per_rider=30,"
echo "  a_true=2.0, seed=11); fit seed=$SEED. Ground-truth difficulty min at 18 kn."
