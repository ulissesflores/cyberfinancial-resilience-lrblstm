"""Resilience and calibration metrics for the LR-BLSTM ablation.

These functions are deliberately framework-agnostic (NumPy only) so they are
unit-testable in isolation from the PyTorch models. They implement the two
headline metrics named in the paper -- **Expected Calibration Error (ECE)** and
the **Resilience Index** -- plus the supporting quantities **recovery time**
and **throughput degradation**.
"""

from __future__ import annotations

import numpy as np


def expected_calibration_error(errors: np.ndarray, stds: np.ndarray, n_bins: int = 10) -> float:
    """Compute regression ECE from predictive standard deviations.

    For a well-calibrated Gaussian predictor, the empirical coverage of the
    ``p``-quantile interval equals ``p``. We bin predictions by expected
    coverage and measure the gap between expected and observed coverage.

    Parameters
    ----------
    errors:
        Signed residuals ``y_true - y_pred``.
    stds:
        Predictive standard deviations (one per prediction); must be positive.
    n_bins:
        Number of probability bins in ``(0, 1)``.

    Returns
    -------
    float
        Mean absolute gap between nominal and empirical coverage across bins
        (0 = perfectly calibrated, larger = worse).
    """
    stds = np.maximum(stds, 1e-9)
    z = np.abs(errors) / stds
    # Two-sided Gaussian coverage for |z|: erf(z / sqrt(2)).
    observed = _erf(z / np.sqrt(2.0))
    quantiles = np.linspace(0.0, 1.0, n_bins + 1)[1:-1]
    gaps = []
    for p in quantiles:
        # Fraction of points whose nominal coverage <= p that are actually
        # covered, compared with the nominal level p.
        empirical = float(np.mean(observed <= p))
        gaps.append(abs(empirical - p))
    return float(np.mean(gaps))


def _erf(x: np.ndarray) -> np.ndarray:
    """Vectorised error function via the Abramowitz-Stegun 7.1.26 approximation.

    Parameters
    ----------
    x:
        Input array (non-negative typical use).

    Returns
    -------
    numpy.ndarray
        ``erf(x)`` with absolute error < 1.5e-7.
    """
    sign = np.sign(x)
    ax = np.abs(x)
    t = 1.0 / (1.0 + 0.3275911 * ax)
    y = 1.0 - (
        ((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592
    ) * t * np.exp(-ax * ax)
    return sign * y


def recovery_time(
    L: np.ndarray, lam: np.ndarray, W: np.ndarray, shock_start: int, tol: float = 0.15
) -> int:
    """Count steps for the queue to re-satisfy Little's Law after a shock.

    Parameters
    ----------
    L, lam, W:
        WIP, arrival-rate, and lead-time series.
    shock_start:
        Index at which the shock begins.
    tol:
        Relative tolerance on the Little residual ``|L - lambda*W| / L``.

    Returns
    -------
    int
        Number of steps after ``shock_start`` until the relative residual stays
        below ``tol``; ``len - shock_start`` if it never recovers (capped).
    """
    n = len(L)
    denom = np.maximum(L[shock_start:], 1e-6)
    rel = np.abs(L[shock_start:] - lam[shock_start:] * W[shock_start:]) / denom
    recovered = rel < tol
    for k in range(len(recovered)):
        if recovered[k:].all():
            return int(k)
    return int(n - shock_start)


def throughput_degradation(served: np.ndarray, baseline: float, shock_slice: slice) -> float:
    """Relative drop in sustained throughput during a shock window.

    Parameters
    ----------
    served:
        Per-step served-work (throughput) series.
    baseline:
        Mean throughput in the calm regime.
    shock_slice:
        Slice selecting the shock window.

    Returns
    -------
    float
        ``1 - mean(served[shock]) / baseline`` clipped to ``[0, 1]`` (0 = no
        degradation, 1 = full collapse).
    """
    shock_mean = float(np.mean(served[shock_slice]))
    deg = 1.0 - shock_mean / max(baseline, 1e-9)
    return float(np.clip(deg, 0.0, 1.0))


def resilience_index(throughput_maintained: float, t_rec: int, t_rec_ref: int) -> float:
    """Combine maintained throughput and recovery speed into one index.

    Operationalises the paper's definition "throughput maintained / recovery
    time under attack" as a dimensionless score in roughly ``[0, 1]``.

    Parameters
    ----------
    throughput_maintained:
        Fraction of baseline throughput retained under attack (``1 - degradation``).
    t_rec:
        Observed recovery time (steps).
    t_rec_ref:
        Reference horizon used to normalise recovery time (e.g. shock length).

    Returns
    -------
    float
        ``throughput_maintained / (1 + t_rec / t_rec_ref)``. Higher is better;
        a fast-recovering, high-throughput system approaches ``throughput_maintained``.
    """
    norm_rec = t_rec / max(t_rec_ref, 1)
    return float(throughput_maintained / (1.0 + norm_rec))
