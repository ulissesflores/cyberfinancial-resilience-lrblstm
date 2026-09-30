"""Antifragile exposure-throttling controller and closed-loop resilience eval.

The paper's third pillar is a feedback controller -- "Safe WIP" / Exposure
Throttling -- that reduces the admitted arrival rate when the predictor signals
instability (a high predicted lead time and/or high epistemic uncertainty). A
convex (preventive) response to disorder is what operationalises antifragility.

To compare the four ablation arms fairly, every arm drives *the same* queue
re-simulation under *the same* shared random stream; only the throttle signal --
derived from that arm's predictions -- differs. A model that anticipates the
lead-time spike and raises uncertainty in time throttles pre-emptively, avoids
queue blow-up, and so retains more throughput and recovers faster.
"""

from __future__ import annotations

import numpy as np


def throttle_signal(
    pred_W: np.ndarray,
    pred_std: np.ndarray,
    w_safe: float,
    beta: float = 1.2,
    gamma: float = 0.8,
) -> np.ndarray:
    """Map predictions to an admission-rate multiplier in ``[throttle_min, 1]``.

    Parameters
    ----------
    pred_W:
        Predicted lead time per step.
    pred_std:
        Predictive standard deviation per step (uncertainty).
    w_safe:
        Target "safe" lead time; predictions above it trigger throttling.
    beta:
        Sensitivity to predicted lead-time excess.
    gamma:
        Sensitivity to predictive uncertainty (Bayesian arms react to "knowing
        that they do not know").

    Returns
    -------
    numpy.ndarray
        Multiplicative throttle in ``[0.2, 1.0]`` per step.
    """
    excess = np.maximum(0.0, pred_W - w_safe) / max(w_safe, 1e-6)
    unc = pred_std / (np.mean(pred_std) + 1e-9)
    raw = 1.0 - beta * excess - gamma * 0.1 * np.maximum(0.0, unc - 1.0)
    return np.clip(raw, 0.2, 1.0)


def closed_loop_resilience(
    lam_shock: np.ndarray,
    mu_shock: np.ndarray,
    throttle: np.ndarray,
    baseline_served: float,
    rng: np.random.Generator,
) -> dict[str, float]:
    """Re-simulate the queue under a throttle and score its resilience.

    Parameters
    ----------
    lam_shock:
        True arrival-rate series over the shocked evaluation window.
    mu_shock:
        Service-rate series over the same window.
    throttle:
        Per-step admission multiplier from :func:`throttle_signal`.
    baseline_served:
        Mean served-work in the calm regime (throughput reference).
    rng:
        Seeded generator; share the *same* seed across arms for a fair contrast.

    Returns
    -------
    dict[str, float]
        ``throughput_maintained`` (fraction of baseline retained) and
        ``t_rec`` (steps until the queue re-satisfies Little's Law).
    """
    n = len(lam_shock)
    queue = 0.0
    served_hist = np.zeros(n)
    L_hist = np.zeros(n)
    lam_adm = lam_shock * throttle
    for t in range(n):
        arrivals = rng.poisson(max(lam_adm[t], 1e-6))
        capacity = rng.poisson(max(mu_shock[t], 1e-6))
        served = min(queue + arrivals, capacity)
        queue = max(0.0, queue + arrivals - served)
        served_hist[t] = served
        L_hist[t] = queue

    throughput_maintained = float(np.clip(np.mean(served_hist) / max(baseline_served, 1e-9), 0, 1))

    # Recovery: steps until WIP settles near the throttled Little equilibrium.
    W_hist = L_hist / np.maximum(lam_adm, 1e-6)
    rel = np.abs(L_hist - lam_adm * W_hist) / np.maximum(L_hist, 1e-6)
    settled = (L_hist < 2.0 * baseline_served) | (rel < 0.15)
    t_rec = n
    for k in range(n):
        if settled[k:].all():
            t_rec = k
            break
    return {"throughput_maintained": throughput_maintained, "t_rec": float(t_rec)}
