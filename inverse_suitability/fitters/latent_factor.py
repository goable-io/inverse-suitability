"""M4 — latent-factor (continuous-item IRT) calibration method.

Fits P(y=1 | rider r, metric x) = sigmoid(a * (theta_r - delta(x))) via
Marginal Maximum Likelihood: integrate theta ~ N(0,1) out with Gauss-Hermite
quadrature, optimise the discrimination `a` and the difficulty grid `delta`
with scipy. Per-rider skill is recovered as the posterior mean over the
quadrature nodes.

Identification: theta is fixed to mean 0, variance 1 by the N(0,1) prior;
delta is anchored (optionally) to an expert prior via a ridge penalty.

This is strictly more general than M3: collapse the theta axis (n_quad=1,
single node at 0) and the marginal reduces to a single logistic curve.

See spec § 2-3."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.polynomial.hermite_e import hermegauss
from scipy.optimize import minimize
from scipy.special import logsumexp

from ..latent_math import sigmoid


@dataclass(frozen=True)
class LatentFit:
    grid: np.ndarray
    difficulty: np.ndarray
    a: float
    theta_mean: dict
    theta_sd: dict
    quad_nodes: np.ndarray
    quad_weights: np.ndarray
    n_train: int
    # Estimated population skill scale (SD of θ). 1.0 in the default
    # mode (fixed-variance identification). In `estimate_skill_scale`
    # mode it is learned: a→1 is fixed instead, and τ carries the scale,
    # so a skill-less cohort collapses τ→0 and produces no phantom skill.
    skill_scale: float = 1.0

    def _interp_delta(self, x: np.ndarray) -> np.ndarray:
        return np.interp(x, self.grid, self.difficulty)

    def predict_prob(self, pseudonym: str, x: float) -> float:
        d = float(self._interp_delta(np.array([x]))[0])
        return float(sigmoid(np.array([self.a * (self.theta_mean[pseudonym] - d)]))[0])

    def population_curve(self, grid_eval: np.ndarray) -> np.ndarray:
        d = self._interp_delta(np.asarray(grid_eval, dtype=float))  # len E
        # sum_q w_q sigmoid(a*(z_q - d))   -> len E
        z = self.quad_nodes[:, None]  # Q×1
        probs = sigmoid(self.a * (z - d[None, :]))  # Q×E
        return self.quad_weights @ probs


def _standard_normal_quadrature(n_quad: int) -> tuple[np.ndarray, np.ndarray]:
    """Gauss-Hermite nodes/weights for theta ~ N(0,1); weights sum to 1."""
    nodes, weights = hermegauss(n_quad)  # weight function exp(-x^2/2)
    weights = weights / np.sqrt(2.0 * np.pi)  # normalise to a probability measure
    return nodes, weights


def fit_latent_factor(
    df,
    *,
    n_grid: int = 8,
    metric_range: tuple[float, float] = (3.0, 35.0),
    n_quad: int = 31,
    delta_prior: np.ndarray | None = None,
    prior_strength: float = 1.0,
    estimate_skill_scale: bool = False,
    seed: int = 0,
) -> LatentFit:
    """Fit M4 by Marginal Maximum Likelihood.

    Default mode (`estimate_skill_scale=False`): the classic IRT
    identification — θ ~ N(0, 1) fixed, discrimination `a` estimated.

    `estimate_skill_scale=True`: the hierarchical reparametrisation —
    `a` is fixed to 1 and the population skill scale τ (the SD of θ) is
    estimated instead. θ = τ·z with z ~ N(0, 1). This breaks the a·τ
    confound the other way and lets the data say "there is no skill
    variation" (τ→0) rather than being forced to assume Var(θ)=1. Kills
    the finite-sample phantom-skill artefact on skill-less cohorts.

    Both modes share one formula: `eta = a · (τ·z − δ(x))`. The scaled
    nodes `τ·z` are stored in `quad_nodes`, so `predict_prob` /
    `population_curve` are identical across modes."""
    grid = np.linspace(metric_range[0], metric_range[1], n_grid)
    nodes, weights = _standard_normal_quadrature(n_quad)
    log_w = np.log(weights)

    riders = sorted(df["pseudonym"].unique().tolist())
    rider_idx = {r: i for i, r in enumerate(riders)}
    metric = df["metric"].to_numpy(dtype=float)
    outcome = df["outcome"].to_numpy(dtype=float)
    obs_rider = df["pseudonym"].map(rider_idx).to_numpy()

    if delta_prior is None:
        delta_prior = np.zeros(n_grid)

    def unpack(params):
        # params[0] is the softplus-raw scale of the FREE scale parameter.
        # Default mode: that free parameter is `a` (τ fixed to 1).
        # estimate_skill_scale: it is `τ` (a fixed to 1).
        free = np.log1p(np.exp(params[0]))  # softplus -> > 0
        delta = params[1:]
        if estimate_skill_scale:
            a, tau = 1.0, free
        else:
            a, tau = free, 1.0
        return a, tau, delta

    def per_obs_logp_matrix(a, tau, delta):
        """Return Q×N log P(y_i | theta=τ·node_q, x_i)."""
        d = np.interp(metric, grid, delta)  # len N
        eta = a * ((tau * nodes)[:, None] - d[None, :])  # Q×N
        p = sigmoid(eta)
        p = np.clip(p, 1e-9, 1 - 1e-9)
        return outcome[None, :] * np.log(p) + (1 - outcome[None, :]) * np.log(1 - p)

    def neg_marginal_ll(params):
        a, tau, delta = unpack(params)
        logp = per_obs_logp_matrix(a, tau, delta)  # Q×N
        Q = nodes.shape[0]
        per_rider = np.zeros((Q, len(riders)))
        np.add.at(per_rider.T, obs_rider, logp.T)  # sum logp into rider columns
        ll_r = logsumexp(log_w[:, None] + per_rider, axis=0)  # len R
        nll = -np.sum(ll_r)
        nll += 0.5 * prior_strength * float(np.sum((delta - delta_prior) ** 2))
        return nll

    rng = np.random.default_rng(seed)
    x0 = np.concatenate([[0.5], delta_prior + 0.01 * rng.standard_normal(n_grid)])
    res = minimize(neg_marginal_ll, x0, method="L-BFGS-B")
    a_hat, tau_hat, delta_hat = unpack(res.x)

    # Scaled nodes carry the skill scale; stored so the LatentFit methods
    # (predict_prob / population_curve) work identically in both modes.
    scaled_nodes = tau_hat * nodes

    # Recover per-rider posterior over theta=τ·z -> mean + sd.
    logp = per_obs_logp_matrix(a_hat, tau_hat, delta_hat)  # Q×N
    Q = nodes.shape[0]
    per_rider = np.zeros((Q, len(riders)))
    np.add.at(per_rider.T, obs_rider, logp.T)
    log_post = log_w[:, None] + per_rider  # Q×R
    log_post -= logsumexp(log_post, axis=0, keepdims=True)
    post = np.exp(log_post)  # Q×R, columns sum to 1
    theta_mean_arr = scaled_nodes @ post  # len R
    theta_var_arr = (scaled_nodes ** 2) @ post - theta_mean_arr ** 2
    theta_sd_arr = np.sqrt(np.clip(theta_var_arr, 0.0, None))

    theta_mean = {r: float(theta_mean_arr[i]) for r, i in rider_idx.items()}
    theta_sd = {r: float(theta_sd_arr[i]) for r, i in rider_idx.items()}

    return LatentFit(
        grid=grid,
        difficulty=delta_hat,
        a=float(a_hat),
        theta_mean=theta_mean,
        theta_sd=theta_sd,
        quad_nodes=scaled_nodes,
        quad_weights=weights,
        n_train=int(len(df)),
        skill_scale=float(tau_hat),
    )
