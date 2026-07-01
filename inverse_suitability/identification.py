"""Identifiability guard for M4. Skill and difficulty separate only when
the rider × condition-bin incidence graph is CONNECTED and dense enough:
riders observed across varied conditions, conditions seen by varied riders.

A rider who only ever rides one condition has unidentified skill (confounded
with always-succeed / always-fail). Below threshold, M4 must auto-disable and
the L3 pipeline falls back to M1-M3.

See spec § 3 (identification & estimation)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class IdentificationReport:
    ok: bool
    reason: str
    n_riders: int
    n_bins: int
    min_conditions_per_rider: int
    min_riders_per_bin: int
    connected: bool


def _connected(rider_ids: list[str], bin_ids: list[int], edges: set[tuple[str, int]]) -> bool:
    """Union-find over the bipartite graph; connected iff all rider+bin
    nodes that appear fall in one component."""
    parent: dict[object, object] = {}

    def find(n):
        parent.setdefault(n, n)
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    def union(x, y):
        parent[find(x)] = find(y)

    nodes_rider = {("r", r) for r in rider_ids}
    nodes_bin = {("b", b) for b in bin_ids}
    for r, b in edges:
        union(("r", r), ("b", b))
    all_nodes = nodes_rider | nodes_bin
    if not all_nodes:
        return False
    roots = {find(n) for n in all_nodes}
    return len(roots) == 1


def check_identification(
    df: pd.DataFrame,
    *,
    n_bins: int = 8,
    metric_range: tuple[float, float] = (3.0, 35.0),
    min_conditions_per_rider: int = 3,
    min_riders_per_bin: int = 3,
) -> IdentificationReport:
    edges_arr = np.linspace(metric_range[0], metric_range[1], n_bins + 1)
    bins = np.clip(np.digitize(df["metric"].to_numpy(), edges_arr[1:-1]), 0, n_bins - 1)
    work = df.assign(_bin=bins)

    conditions_per_rider = work.groupby("pseudonym")["_bin"].nunique()
    riders_per_bin = work.groupby("_bin")["pseudonym"].nunique()

    n_riders = int(work["pseudonym"].nunique())
    present_bins = sorted(int(b) for b in work["_bin"].unique())
    n_bins_present = len(present_bins)
    min_cpr = int(conditions_per_rider.min()) if len(conditions_per_rider) else 0
    min_rpb = int(riders_per_bin.min()) if len(riders_per_bin) else 0

    edges = set(zip(work["pseudonym"].tolist(), work["_bin"].astype(int).tolist()))
    connected = _connected(
        sorted(work["pseudonym"].unique().tolist()), present_bins, edges
    )

    reason = "ok"
    ok = True
    if min_cpr < min_conditions_per_rider:
        ok, reason = False, f"min_conditions_per_rider {min_cpr} < {min_conditions_per_rider}"
    elif min_rpb < min_riders_per_bin:
        ok, reason = False, f"min_riders_per_bin {min_rpb} < {min_riders_per_bin}"
    elif not connected:
        ok, reason = False, "incidence_graph_disconnected"

    return IdentificationReport(
        ok=ok,
        reason=reason,
        n_riders=n_riders,
        n_bins=n_bins_present,
        min_conditions_per_rider=min_cpr,
        min_riders_per_bin=min_rpb,
        connected=connected,
    )


# ---------------------------------------------------------------------------
# Per-rider data-sufficiency gate (L15 wrinkle T1).
# ---------------------------------------------------------------------------
# `check_identification` gates the COHORT fit. This gate is narrower: given a
# fitted model, should we SURFACE an individual rider's θ in scoring? A rider
# with one or two sessions has a θ that is mostly prior (wide sd) — acting on
# it is false precision. Below the floor, score the rider at population /
# caller-provided level instead. This sidesteps the weak per-rider sd
# calibration (T11) by gating on observation COUNT + condition spread, which
# are always reliable regardless of how well the posterior sd is calibrated.
MIN_PERSONAL_THETA_OBS = 5
MIN_PERSONAL_THETA_CONDITIONS = 3


def is_personal_theta_usable(
    n_obs: int,
    n_distinct_conditions: int,
    *,
    min_obs: int = MIN_PERSONAL_THETA_OBS,
    min_conditions: int = MIN_PERSONAL_THETA_CONDITIONS,
) -> bool:
    """True iff a rider has enough observations across enough distinct
    conditions for their personal θ to be worth using. A rider who fails
    this is scored at population / explicit-level — never on a noisy
    1-or-2-session skill estimate."""
    return n_obs >= min_obs and n_distinct_conditions >= min_conditions
