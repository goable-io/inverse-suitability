#!/usr/bin/env python3
"""Turn the `latent-demo` stats.json into sections/results.tex.

The paper NEVER hard-codes recovery numbers. This script reads the JSON emitted
by `inverse-suitability latent-demo` and writes a LaTeX file containing:

  1. \\newcommand macros for every recovered quantity (cited inline in prose), and
  2. a booktabs results table.

Ground-truth DGP parameters (the true difficulty minimum at 18 kn, a_true = 2.0,
the 80x30 cohort) are NOT written here -- they live as fixed prose in
05-synthetic-recovery.tex and the appendix. This file carries only the ESTIMATED
/ recovered values. Do not conflate the two: prose declares truth, this table
reports recovery.

Usage:
    python gen_results_tex.py <stats.json> <out.tex>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _fmt(x: float, places: int) -> str:
    return f"{x:.{places}f}"


def render(stats: dict) -> str:
    corr = float(stats["theta_recovery_corr"])
    dmin = float(stats["difficulty_min_knots"])
    a = float(stats["discrimination_a"])
    bss = float(stats["held_out_bss"])
    n_train = int(stats["n_train"])
    marginal = bool(stats["marginal_matches"])
    ident = bool(stats["identification_ok"])

    yn = lambda b: r"\checkmark" if b else r"$\times$"  # noqa: E731

    return f"""% !!! GENERATED FILE -- DO NOT EDIT BY HAND !!!
% Produced by reproducibility/gen_results_tex.py from the stats.json that
% `inverse-suitability latent-demo` writes. Regenerate with `make repro`.
% Every value below is a RECOVERED estimate; ground-truth DGP parameters are
% stated as fixed prose in the surrounding section, never here.
%
% Inline macros (used in 05-synthetic-recovery.tex prose):
\\newcommand{{\\thetaRecoveryCorr}}{{{_fmt(corr, 2)}}}
\\newcommand{{\\thetaRecoveryCorrFull}}{{{_fmt(corr, 4)}}}
\\newcommand{{\\difficultyMinKnots}}{{{_fmt(dmin, 1)}}}
\\newcommand{{\\discriminationA}}{{{_fmt(a, 2)}}}
\\newcommand{{\\heldOutBSS}}{{{_fmt(bss, 3)}}}
% signed, WITHOUT math delimiters -- wrap in $...$ at the call site.
\\newcommand{{\\heldOutBSSsigned}}{{+{_fmt(bss, 2)}}}
\\newcommand{{\\nTrain}}{{{n_train:,}}}
%
\\begin{{table}}[t]
  \\centering
  \\caption{{Synthetic recovery on the reference cohort ($80$ riders $\\times\\,30$
  paired outcomes, $n_{{\\text{{train}}}} = {n_train:,}$). Every value is recovered
  from behavioural outcomes alone by marginal maximum likelihood; none is supplied
  to the fit. The data-generating difficulty is minimised at the ground-truth
  optimum $x^\\star = 18$~kn with true discrimination $a_{{\\text{{true}}}} = 2.0$
  (stated in the text, not fit here). Reproduced by a single command
  (\\texttt{{inverse-suitability latent-demo}}); see Appendix.}}
  \\label{{tab:recovery}}
  \\begin{{tabular}}{{@{{}}llr@{{}}}}
    \\toprule
    Quantity & Symbol & Recovered \\\\
    \\midrule
    Latent-skill recovery (Pearson) & $\\mathrm{{corr}}(\\theta,\\hat\\theta)$ & {_fmt(corr, 3)} \\\\
    Difficulty-minimum location     & $\\hat{{x}}^\\star$ (kn)               & {_fmt(dmin, 1)} \\\\
    Discrimination                  & $\\hat{{a}}$                          & {_fmt(a, 2)} \\\\
    Held-out Brier skill score      & $\\mathrm{{BSS}}$ vs.\\ single curve   & $+{_fmt(bss, 3)}$ \\\\
    Marginal matches single curve   & --                                    & {yn(marginal)} \\\\
    Identification gate passed      & --                                    & {yn(ident)} \\\\
    \\bottomrule
  \\end{{tabular}}
\\end{{table}}
"""


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    stats = json.loads(Path(sys.argv[1]).read_text())
    Path(sys.argv[2]).write_text(render(stats))
    print(f"wrote {sys.argv[2]} from {sys.argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
