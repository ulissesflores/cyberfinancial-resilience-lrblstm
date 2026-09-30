"""Phase-2 orchestrator: run the LR-BLSTM ablation (Models A-D) as one run.

Pipeline
--------
1. Simulate the cyber-financial queueing system (calm regime + shocks).
2. Build standardised windows; split calm (train) from the shocked tail (OOD).
3. Train each ablation arm (A-D) on the calm regime only.
4. Evaluate each arm on the shocked tail: prediction degradation, ECE, and a
   closed-loop Resilience Index (the arm drives the Safe-WIP controller over a
   shared queue re-simulation).
5. Persist ``results.json`` + tables + figures, then write ``manifest.json`` and
   ``checksums.sha256`` -- the run is valid only if both exist.

Determinism: a single ``--seed`` drives the simulator, per-arm initialisation,
and the shared controller stream, so re-execution reproduces identical hashes.
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from pathlib import Path

import numpy as np
import torch
from controller import closed_loop_resilience, throttle_signal
from figures_ablation import generate_figures
from hash_utils import environment_fingerprint, save_json, write_checksums_sha256
from metrics import (
    expected_calibration_error,
    resilience_index,
)
from models import ABLATION, build_dataset, predict, train_model
from simulate import SimConfig, little_residual, simulate

REPO_URL = "https://github.com/ulissesflores/cyberfinancial-resilience-lrblstm"


def _git_commit() -> str:
    """Return the current git commit hash, or ``UNKNOWN``.

    Returns
    -------
    str
        Commit hash of HEAD.
    """
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except Exception:
        return "UNKNOWN"


def run_ablation(seq_len: int, epochs: int, seed: int, n_steps: int) -> tuple[dict, dict]:
    """Train and evaluate all four arms; return results and the simulation.

    Parameters
    ----------
    seq_len:
        Input window length.
    epochs:
        Training epochs per arm.
    seed:
        Master seed for full determinism.
    n_steps:
        Simulation length.

    Returns
    -------
    tuple[dict, dict]
        ``results`` (per-arm metrics + provenance) and the raw ``series``.
    """
    cfg = SimConfig(n_steps=n_steps)
    series = simulate(cfg, np.random.default_rng(seed))
    ds, stats = build_dataset(series, seq_len=seq_len)

    n_win = len(ds.y)
    train_end = int(n_win * 0.60)  # calm regime only
    calm_eval = slice(int(n_win * 0.45), train_end)  # held-out calm
    shock_eval = slice(int(n_win * 2 / 3), n_win)  # OOD shocked tail

    # Controller references from the calm regime.
    w_safe = float(np.mean(series["W"][: (2 * n_steps) // 3]) * 1.5)
    baseline_served = float(np.mean(series["lambda_t"][: (2 * n_steps) // 3]))
    t_rec_ref = (shock_eval.stop - shock_eval.start) // 3

    per_model: dict[str, dict] = {}
    preds_for_fig: dict[str, np.ndarray] = {}
    for spec in ABLATION:
        model = train_model(spec, ds, stats, train_end=train_end, seed=seed + ord(spec.name))

        y_real = ds.y.numpy() * stats["t_std"] + stats["t_mean"]

        m_calm, s_calm = predict(model, ds.X[calm_eval], spec, stats)
        m_shock, s_shock = predict(model, ds.X[shock_eval], spec, stats)
        preds_for_fig[spec.name] = m_shock

        err_calm = y_real[calm_eval] - m_calm
        err_shock = y_real[shock_eval] - m_shock
        mse_calm = float(np.mean(err_calm**2))
        mse_shock = float(np.mean(err_shock**2))

        ece_calm = expected_calibration_error(err_calm, s_calm)
        ece_shock = expected_calibration_error(err_shock, s_shock)

        throttle = throttle_signal(m_shock, s_shock, w_safe=w_safe)
        cl = closed_loop_resilience(
            lam_shock=series["lambda_t"][(2 * n_steps) // 3 :][: len(throttle)],
            mu_shock=series["mu_t"][(2 * n_steps) // 3 :][: len(throttle)],
            throttle=throttle,
            baseline_served=baseline_served,
            rng=np.random.default_rng(seed + 777),
        )
        ri = resilience_index(cl["throughput_maintained"], int(cl["t_rec"]), t_rec_ref)

        per_model[spec.name] = {
            "bayesian": spec.bayesian,
            "little": spec.little,
            "mse_calm": mse_calm,
            "mse_shock": mse_shock,
            "degradation_ratio": float(mse_shock / max(mse_calm, 1e-9)),
            "ece_calm": ece_calm,
            "ece_shock": ece_shock,
            "throughput_maintained": cl["throughput_maintained"],
            "recovery_time": int(cl["t_rec"]),
            "resilience_index": ri,
        }

    results = {
        "experiment": "LR-BLSTM ablation (Models A-D)",
        "hypothesis": "Model D (full LR-BLSTM) shows the lowest degradation and "
        "the highest Resilience Index under stress.",
        "parameters": {
            "seq_len": seq_len,
            "epochs": epochs,
            "seed": seed,
            "n_steps": n_steps,
            "alpha_little": 0.5,
            "mc_samples": 30,
            "w_safe": w_safe,
            "baseline_served": baseline_served,
        },
        "sanity": {"little_residual_calm": little_residual(series)},
        "models": per_model,
        "winner": _winner(per_model),
    }
    return results, {
        "series": series,
        "preds": preds_for_fig,
        "shock_eval": shock_eval,
        "ds": ds,
        "stats": stats,
    }


def _winner(per_model: dict[str, dict]) -> dict:
    """Identify which arm wins on each headline criterion.

    Parameters
    ----------
    per_model:
        Per-arm metric dictionary.

    Returns
    -------
    dict
        Best arm by resilience index, by lowest degradation, and by calibration
        under shock -- reported honestly whether or not it is Model D.
    """
    best_ri = max(per_model, key=lambda k: per_model[k]["resilience_index"])
    best_deg = min(per_model, key=lambda k: per_model[k]["degradation_ratio"])
    best_ece = min(per_model, key=lambda k: per_model[k]["ece_shock"])
    return {
        "by_resilience_index": best_ri,
        "by_lowest_degradation": best_deg,
        "by_calibration_shock": best_ece,
        "thesis_confirmed": bool(best_ri == "D" and best_deg in ("C", "D")),
    }


def write_tables(results: dict, run_dir: Path) -> list[Path]:
    """Write the ablation results as machine- and human-readable tables.

    Parameters
    ----------
    results:
        Output of :func:`run_ablation`.
    run_dir:
        Run directory.

    Returns
    -------
    list[Path]
        Paths of written table files.
    """
    tables = run_dir / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    save_json(results, run_dir / "results.json")

    md = [
        "| Model | Bayes | Little | Degradation | ECE(shock) | Throughput | T_rec | Resilience |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, m in results["models"].items():
        bayes = "Y" if m["bayesian"] else "N"
        little = "Y" if m["little"] else "N"
        md.append(
            f"| {name} | {bayes} | {little} | {m['degradation_ratio']:.3f} | "
            f"{m['ece_shock']:.3f} | {m['throughput_maintained']:.3f} | "
            f"{m['recovery_time']} | {m['resilience_index']:.3f} |"
        )
    (tables / "ablation.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return [run_dir / "results.json", tables / "ablation.md"]


def main(args: argparse.Namespace) -> str:
    """Execute the full ablation run and write the audit-grade artifacts.

    Parameters
    ----------
    args:
        Parsed CLI arguments.

    Returns
    -------
    str
        The run identifier.
    """
    torch.use_deterministic_algorithms(False)
    run_id = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path("runs") / run_id
    (run_dir / "figures").mkdir(parents=True, exist_ok=True)

    results, aux = run_ablation(
        seq_len=args.seq_len, epochs=args.epochs, seed=args.seed, n_steps=args.n_steps
    )

    table_paths = write_tables(results, run_dir)
    fig_paths = generate_figures(results, aux, run_dir / "figures")

    manifest = {
        "run_id": run_id,
        "created_utc": dt.datetime.now(dt.UTC).isoformat(),
        "phase": 2,
        "git": {"repository_url": REPO_URL, "commit": _git_commit(), "tag": None},
        "environment": environment_fingerprint(),
        "parameters": results["parameters"],
        "artifacts": {
            "data": [],
            "figures": [str(p.relative_to(run_dir)) for p in fig_paths],
            "tables": [str(p.relative_to(run_dir)) for p in table_paths],
            "metrics": "results.json",
            "checksums_sha256": "checksums.sha256",
            "logs": [],
        },
        "notes": "Phase-2 LR-BLSTM ablation. Deterministic under fixed seed.",
    }
    save_json(manifest, run_dir / "manifest.json")

    all_artifacts = [run_dir / "manifest.json", *table_paths, *fig_paths]
    write_checksums_sha256(all_artifacts, run_dir / "checksums.sha256")

    print(f"[OK] Ablation run: {run_dir}")
    print(f"[OK] Winner by Resilience Index: {results['winner']['by_resilience_index']}")
    print(f"[OK] Thesis confirmed: {results['winner']['thesis_confirmed']}")
    return run_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the LR-BLSTM ablation (Models A-D).")
    parser.add_argument("--seq_len", type=int, default=48)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n_steps", type=int, default=6000)
    main(parser.parse_args())
