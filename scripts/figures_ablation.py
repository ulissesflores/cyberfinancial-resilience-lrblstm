"""Figure generation for the LR-BLSTM ablation.

Every figure maps to a specific claim in the paper (no orphan figures):

- ``fig1_resilience_index``  -> Model D attains the highest Resilience Index.
- ``fig2_degradation``       -> physics-regularised arms (C, D) degrade least.
- ``fig3_calibration``       -> Bayesian arms (B, D) keep ECE low under shock.
- ``fig4_predictions``       -> D tracks the true lead time best in the shock.
- ``fig5_little_regime``     -> Little's Law holds in the calm regime and is
                                stressed by the injected shocks (data sanity).

Each figure is written in vector (PDF, SVG) and raster (PNG) form.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

_ORDER = ("A", "B", "C", "D")
_COLORS = {"A": "#9aa0a6", "B": "#4c8bf5", "C": "#34a853", "D": "#ea4335"}


def _save(fig: plt.Figure, out_dir: Path, stem: str) -> list[Path]:
    """Write one figure as PDF, SVG and PNG and return the paths.

    Parameters
    ----------
    fig:
        Matplotlib figure.
    out_dir:
        Target directory.
    stem:
        File name without extension.

    Returns
    -------
    list[Path]
        The three written paths.
    """
    paths = []
    for ext in ("pdf", "svg", "png"):
        p = out_dir / f"{stem}.{ext}"
        fig.savefig(p, bbox_inches="tight", dpi=150)
        paths.append(p)
    plt.close(fig)
    return paths


def generate_figures(results: dict, aux: dict, out_dir: Path) -> list[Path]:
    """Generate all ablation figures from results and auxiliary arrays.

    Parameters
    ----------
    results:
        Output of ``run_ablation`` (per-model metrics).
    aux:
        Dict with ``series`` (simulation), ``preds`` (per-model shock
        predictions), ``shock_eval`` (slice), ``ds`` and ``stats``.
    out_dir:
        Directory to write figures into.

    Returns
    -------
    list[Path]
        All written figure paths (PDF + SVG + PNG per figure).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    models = results["models"]
    paths: list[Path] = []

    # fig1 -- Resilience Index per model.
    fig, ax = plt.subplots(figsize=(6, 4))
    vals = [models[m]["resilience_index"] for m in _ORDER]
    ax.bar(_ORDER, vals, color=[_COLORS[m] for m in _ORDER])
    ax.set_ylabel("Resilience Index")
    ax.set_xlabel("Ablation arm")
    ax.set_title("Resilience Index under stress (higher is better)")
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:.3f}", ha="center", va="bottom", fontsize=9)
    paths += _save(fig, out_dir, "fig1_resilience_index")

    # fig2 -- Degradation ratio per model.
    fig, ax = plt.subplots(figsize=(6, 4))
    vals = [models[m]["degradation_ratio"] for m in _ORDER]
    ax.bar(_ORDER, vals, color=[_COLORS[m] for m in _ORDER])
    ax.set_ylabel("Degradation ratio (MSE shock / MSE calm)")
    ax.set_xlabel("Ablation arm")
    ax.set_title("Prediction degradation under stress (lower is better)")
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
    paths += _save(fig, out_dir, "fig2_degradation")

    # fig3 -- Calibration (ECE) calm vs shock.
    fig, ax = plt.subplots(figsize=(6, 4))
    x = np.arange(len(_ORDER))
    ax.bar(x - 0.2, [models[m]["ece_calm"] for m in _ORDER], 0.4, label="calm", color="#cccccc")
    ax.bar(x + 0.2, [models[m]["ece_shock"] for m in _ORDER], 0.4, label="shock", color="#ea4335")
    ax.set_xticks(x)
    ax.set_xticklabels(_ORDER)
    ax.set_ylabel("Expected Calibration Error")
    ax.set_xlabel("Ablation arm")
    ax.set_title("Calibration: calm vs shock (lower is better)")
    ax.legend()
    paths += _save(fig, out_dir, "fig3_calibration")

    # fig4 -- Predicted vs true lead time in the shocked window.
    series = aux["series"]
    ds = aux["ds"]
    stats = aux["stats"]
    shock_eval = aux["shock_eval"]
    y_real = ds.y.numpy() * stats["t_std"] + stats["t_mean"]
    true_shock = y_real[shock_eval]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(true_shock, color="black", lw=1.4, label="true W")
    for m in _ORDER:
        ax.plot(aux["preds"][m], color=_COLORS[m], lw=0.9, alpha=0.85, label=f"pred {m}")
    ax.set_ylabel("Lead time W")
    ax.set_xlabel("Step (shocked window)")
    ax.set_title("Lead-time tracking under stress")
    ax.legend(ncol=3, fontsize=8)
    paths += _save(fig, out_dir, "fig4_predictions")

    # fig5 -- Little's Law regime: L vs lambda*W over the full trajectory.
    n = len(series["L"])
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(series["L"], color="#4c8bf5", lw=0.7, label="L (WIP)")
    ax.plot(
        series["lambda_t"] * series["W"], color="#34a853", lw=0.7, alpha=0.7, label="lambda * W"
    )
    ax.axvline((2 * n) // 3, color="#ea4335", ls="--", lw=1.0, label="shock onset")
    ax.set_ylabel("Queue length")
    ax.set_xlabel("Step")
    ax.set_title("Little's Law invariant: holds in calm regime, stressed by shocks")
    ax.legend(fontsize=8)
    paths += _save(fig, out_dir, "fig5_little_regime")

    return paths
