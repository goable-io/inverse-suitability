"""Minimal CLI for the Inverse Suitability reproducibility package.

Exposes ONLY the ``latent-demo`` command -- the synthetic-recovery artifact that
reproduces the paper's results. The full L3 calibration CLI (weekly runs, cell
evaluation, config validation, PR generation) is part of Goable's private engine
and is deliberately not included here.
"""

from __future__ import annotations

import json
from pathlib import Path

import click


@click.group()
def main() -> None:
    """Inverse Suitability -- public reproducibility CLI."""


@main.command("latent-demo")
@click.option(
    "--out",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("./latent_demo_output"),
    help="Directory where stats.json is written.",
)
@click.option(
    "--seed",
    type=int,
    default=0,
    help="Deterministic seed for the fit (cohort generation uses its own internal seed).",
)
def latent_demo(out: Path, seed: int) -> None:
    """Run the inverse-suitability (M4) demo on a synthetic two-factor cohort.

    Generates a cohort with KNOWN per-rider theta + KNOWN difficulty delta(x),
    runs the identification guard + latent-factor fit + validation gates
    end-to-end, and writes stats.json. This is the reproducibility artifact for
    the paper -- synthetic data only, no proprietary observations.
    """
    from .latent_demo import run_latent_demo

    click.echo("\n=== Inverse Suitability -- synthetic two-factor cohort ===\n")
    stats = run_latent_demo(str(out), seed=seed)
    click.echo(json.dumps(stats, indent=2))
    click.echo(f"\nstats.json written to {out}/stats.json")


if __name__ == "__main__":
    main()
