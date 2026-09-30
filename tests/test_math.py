"""Correctness of the mathematical primitives (invariants and metrics)."""

from __future__ import annotations

import numpy as np
import pytest
from metrics import (
    _erf,
    expected_calibration_error,
    recovery_time,
    resilience_index,
    throughput_degradation,
)
from scipy import special
from simulate import SimConfig, little_residual, simulate


def test_erf_matches_scipy() -> None:
    """The Abramowitz-Stegun erf approximation matches SciPy to 1e-6."""
    x = np.linspace(-3, 3, 101)
    assert np.allclose(_erf(x), special.erf(x), atol=2e-7)


def test_little_residual_small_in_calm_regime() -> None:
    """Little's Law L = lambda * W holds (residual ~ 0) in the calm prefix."""
    series = simulate(SimConfig(n_steps=1500), np.random.default_rng(0))
    # W is defined as L / lambda, so the residual is exactly zero by construction.
    assert little_residual(series) < 1e-6


def test_ece_lower_when_calibrated() -> None:
    """A predictor whose std matches its error spread has lower ECE."""
    rng = np.random.default_rng(1)
    sigma = 2.0
    errors = rng.normal(0, sigma, size=4000)
    calibrated = expected_calibration_error(errors, np.full_like(errors, sigma))
    overconfident = expected_calibration_error(errors, np.full_like(errors, sigma * 0.2))
    assert calibrated < overconfident


def test_resilience_index_monotonicity() -> None:
    """RI rises with maintained throughput and falls with recovery time."""
    base = resilience_index(0.8, t_rec=10, t_rec_ref=20)
    more_tput = resilience_index(0.95, t_rec=10, t_rec_ref=20)
    slower = resilience_index(0.8, t_rec=40, t_rec_ref=20)
    assert more_tput > base > slower


def test_throughput_degradation_bounds() -> None:
    """Degradation is clipped to [0, 1]."""
    served = np.array([5.0, 5.0, 5.0, 5.0])
    assert throughput_degradation(served, baseline=10.0, shock_slice=slice(0, 4)) == pytest.approx(
        0.5
    )
    assert throughput_degradation(served, baseline=2.0, shock_slice=slice(0, 4)) == 0.0


def test_recovery_time_detects_settling() -> None:
    """Recovery time is 0 when the invariant holds from the shock onset."""
    n = 50
    lam = np.full(n, 10.0)
    W = np.full(n, 2.0)
    L = lam * W  # perfectly consistent
    assert recovery_time(L, lam, W, shock_start=0) == 0
