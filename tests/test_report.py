"""Figure and table generation produce the expected artifacts."""

from __future__ import annotations

import numpy as np
from figures_ablation import generate_figures
from models import build_dataset
from simulate import SimConfig, simulate


def _fake_results() -> dict:
    """Build a minimal results dict covering all four arms.

    Returns
    -------
    dict
        Per-model metrics with the keys the figures consume.
    """
    models = {}
    for i, name in enumerate("ABCD"):
        models[name] = {
            "bayesian": name in ("B", "D"),
            "little": name in ("C", "D"),
            "degradation_ratio": 3.0 - 0.5 * i,
            "ece_calm": 0.05,
            "ece_shock": 0.20 - 0.03 * i,
            "throughput_maintained": 0.6 + 0.05 * i,
            "recovery_time": 30 - 4 * i,
            "resilience_index": 0.4 + 0.08 * i,
        }
    return {"models": models}


def test_generate_figures_writes_vector_and_raster(tmp_path) -> None:
    """generate_figures writes PDF + SVG + PNG for every figure."""
    series = simulate(SimConfig(n_steps=900), np.random.default_rng(0))
    ds, stats = build_dataset(series, seq_len=24)
    shock_eval = slice(int(len(ds.y) * 2 / 3), len(ds.y))
    preds = {m: np.zeros(shock_eval.stop - shock_eval.start) for m in "ABCD"}
    aux = {"series": series, "preds": preds, "shock_eval": shock_eval, "ds": ds, "stats": stats}

    paths = generate_figures(_fake_results(), aux, tmp_path)

    stems = {p.stem for p in paths}
    assert stems == {
        "fig1_resilience_index",
        "fig2_degradation",
        "fig3_calibration",
        "fig4_predictions",
        "fig5_little_regime",
    }
    for stem in stems:
        for ext in ("pdf", "svg", "png"):
            assert (tmp_path / f"{stem}.{ext}").exists()
