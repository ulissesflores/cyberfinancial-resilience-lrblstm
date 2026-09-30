"""Discrete-event simulation of a cyber-financial queueing system.

Scientific intent
------------------
Phase 2 of the project requires a controlled, reproducible data-generating
process in which Little's Law (``L = lambda * W``) holds in the calm regime and
is *stressed* by adversarial / volatility shocks. Public market data (Phase 1)
cannot expose the internal queue variables (L, lambda, W) directly, so the
ablation study (Models A-D) is run on a simulator whose ground truth is known.

The simulator follows the protocol stated in the paper:
- prices via **jump-diffusion** (geometric Brownian motion + compound Poisson
  jumps);
- arrivals via a **non-homogeneous Poisson** process (diurnal intensity);
- three controlled shocks: **volumetric burst** (lambda spike), **latency
  injection** (service-rate degradation), and **adversarial noise** (telemetry
  poisoning), plus an abrupt **concept drift** of the liquidity regime.

Determinism: every function takes an explicit ``numpy.random.Generator`` (seeded
upstream), so a fixed seed reproduces bit-identical trajectories.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class ShockWindow:
    """A time window during which a stress factor is applied.

    Parameters
    ----------
    kind:
        Shock type: ``"burst"`` (arrival spike), ``"latency"`` (service-rate
        degradation), ``"adversarial"`` (telemetry noise), or ``"drift"``
        (abrupt regime change).
    start:
        First timestep index (inclusive) of the window.
    end:
        Last timestep index (exclusive) of the window.
    magnitude:
        Multiplicative intensity of the shock (semantics depend on ``kind``).
    """

    kind: str
    start: int
    end: int
    magnitude: float


@dataclass
class SimConfig:
    """Configuration of the cyber-financial simulation.

    Defaults reproduce the regime described in the paper's methodology and are
    sized so a full Models A-D ablation runs on CPU in minutes while remaining a
    faithful, falsifiable test of the LR-BLSTM thesis.
    """

    n_steps: int = 6000
    base_lambda: float = 40.0
    base_mu: float = 44.0
    diurnal_amplitude: float = 0.35
    diurnal_period: int = 480
    price_s0: float = 30000.0
    price_drift: float = 0.00002
    price_sigma: float = 0.012
    jump_intensity: float = 0.01
    jump_sigma: float = 0.03
    warmup: int = 200
    shocks: list[ShockWindow] = field(default_factory=list)

    @staticmethod
    def default_shocks(n_steps: int) -> list[ShockWindow]:
        """Build the canonical shock schedule used by the ablation.

        Parameters
        ----------
        n_steps:
            Total simulation length; shock windows are placed in the final
            (out-of-distribution) third so the models are trained on the calm
            regime and evaluated under stress.

        Returns
        -------
        list[ShockWindow]
            Volumetric burst, latency injection, adversarial noise, and an
            abrupt concept-drift window.
        """
        q = n_steps // 12
        base = (2 * n_steps) // 3
        return [
            ShockWindow("burst", base, base + q, 11.0),
            ShockWindow("latency", base + 2 * q, base + 3 * q, 0.30),
            ShockWindow("adversarial", base + 3 * q, base + 4 * q, 0.20),
            ShockWindow("drift", base, n_steps, 1.0),
        ]


def _active(windows: list[ShockWindow], kind: str, t: int) -> float:
    """Return the magnitude of an active shock of ``kind`` at time ``t``.

    Parameters
    ----------
    windows:
        All configured shock windows.
    kind:
        Shock type to test for.
    t:
        Current timestep.

    Returns
    -------
    float
        The shock magnitude if a window of ``kind`` covers ``t``; otherwise the
        neutral value (``0.0`` for ``adversarial``, ``1.0`` otherwise).
    """
    neutral = 0.0 if kind == "adversarial" else 1.0
    for w in windows:
        if w.kind == kind and w.start <= t < w.end:
            return w.magnitude
    return neutral


def simulate(cfg: SimConfig, rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Run the discrete-event cyber-financial queueing simulation.

    Parameters
    ----------
    cfg:
        Simulation configuration (rates, price dynamics, shock schedule).
    rng:
        Seeded NumPy generator; identical seeds reproduce identical output.

    Returns
    -------
    dict[str, numpy.ndarray]
        Per-timestep arrays: ``lambda_t`` (arrival rate), ``mu_t`` (service
        rate), ``L`` (WIP / queue length), ``W`` (lead time), ``price``,
        ``ret`` (log returns), ``vol`` (rolling volatility proxy), and
        ``obs_W`` (telemetry-observed lead time, adversarially corrupted inside
        the adversarial window).

    Notes
    -----
    The queue obeys ``L_{t+1} = max(0, L_t + arrivals - served)`` with
    ``served ~ Poisson(mu_t)`` capped by available work, so in the calm regime
    the empirical mean satisfies Little's Law ``mean(L) ~= mean(lambda)*mean(W)``.
    """
    n = cfg.n_steps
    shocks = cfg.shocks or SimConfig.default_shocks(n)

    lam = np.zeros(n)
    mu = np.zeros(n)
    queue = np.zeros(n)
    lead = np.zeros(n)
    price = np.zeros(n)
    obs_lead = np.zeros(n)

    price[0] = cfg.price_s0
    drift_phase = 0.0

    for t in range(n):
        # Non-homogeneous Poisson intensity with a diurnal component; concept
        # drift shifts the phase abruptly, changing the liquidity regime.
        if _active(shocks, "drift", t) > 0 and t == (2 * n) // 3:
            drift_phase = np.pi
        diurnal = 1.0 + cfg.diurnal_amplitude * np.sin(
            2 * np.pi * t / cfg.diurnal_period + drift_phase
        )
        burst = _active(shocks, "burst", t)
        lam_t = cfg.base_lambda * diurnal * burst
        lam[t] = lam_t

        # Service rate degraded during the latency-injection window.
        mu[t] = cfg.base_mu * _active(shocks, "latency", t)

        arrivals = rng.poisson(max(lam_t, 1e-6))
        capacity = rng.poisson(max(mu[t], 1e-6))
        prev_L = queue[t - 1] if t > 0 else 0.0
        served = min(prev_L + arrivals, capacity)
        queue[t] = max(0.0, prev_L + arrivals - served)

        # Lead time via Little's Law W = L / lambda (with a small floor on rate).
        lead[t] = queue[t] / max(lam_t, 1e-6)

        # Jump-diffusion price path.
        if t > 0:
            z = rng.standard_normal()
            jump = 0.0
            if rng.random() < cfg.jump_intensity:
                jump = cfg.jump_sigma * rng.standard_normal()
            log_ret = (cfg.price_drift - 0.5 * cfg.price_sigma**2) + cfg.price_sigma * z + jump
            price[t] = price[t - 1] * np.exp(log_ret)

        # Telemetry observation: adversarial poisoning adds noise inside window.
        adv = _active(shocks, "adversarial", t)
        obs_lead[t] = lead[t] * (1.0 + adv * rng.standard_normal()) if adv > 0 else lead[t]

    ret = np.zeros(n)
    ret[1:] = np.diff(np.log(np.maximum(price, 1e-9)))
    vol = _rolling_std(ret, window=30)

    return {
        "lambda_t": lam,
        "mu_t": mu,
        "L": queue,
        "W": lead,
        "obs_W": obs_lead,
        "price": price,
        "ret": ret,
        "vol": vol,
    }


def _rolling_std(x: np.ndarray, window: int) -> np.ndarray:
    """Compute a causal rolling standard deviation (volatility proxy).

    Parameters
    ----------
    x:
        Input series (log returns).
    window:
        Look-back length.

    Returns
    -------
    numpy.ndarray
        Rolling standard deviation, left-padded with the first valid value.
    """
    n = len(x)
    out = np.zeros(n)
    for t in range(n):
        lo = max(0, t - window + 1)
        out[t] = np.std(x[lo : t + 1]) if t > 0 else 0.0
    return out


def little_residual(series: dict[str, np.ndarray]) -> float:
    """Mean absolute violation of Little's Law over the calm regime.

    Parameters
    ----------
    series:
        Output of :func:`simulate`.

    Returns
    -------
    float
        ``mean(|L - lambda * W|)`` restricted to the in-distribution prefix
        (before the first shock); should be ~0 by construction.
    """
    n = len(series["L"])
    cut = (2 * n) // 3
    resid = np.abs(series["L"][:cut] - series["lambda_t"][:cut] * series["W"][:cut])
    return float(np.mean(resid))
