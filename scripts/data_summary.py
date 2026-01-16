#!/usr/bin/env python3
"""Audit-grade data summary generator for Phase 1.

Outputs (run contract):
- runs/<run_id>/tables/data_summary.md
- runs/<run_id>/tables/data_summary.csv
- runs/<run_id>/tables/data_summary.json
- manifest.json updated (artifacts.tables + parameters.data_summary)
- checksums.sha256 updated to include tables + manifest (+ existing artifacts)

Scientific intent:
- Provide Methods/Data-ready descriptive tables with explicit scope/limits.
- Avoid causal claims. Everything is descriptive.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd
from hash_utils import save_json, write_checksums_sha256


def utcnow_iso() -> str:
    """Return current UTC time as an ISO-8601 string.

    Returns
    -------
    str
        ISO-8601 formatted UTC timestamp.
    """
    return dt.datetime.now(dt.UTC).isoformat()


def load_manifest(run_dir: Path) -> dict:
    """Load the run manifest from the specified directory.

    Parameters
    ----------
    run_dir : Path
        Directory containing the `manifest.json`.

    Returns
    -------
    dict
        Parsed manifest dictionary.
    """
    return json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))


def update_manifest(run_dir: Path, manifest: dict) -> None:
    """Persist the updated manifest to the run directory.

    Parameters
    ----------
    run_dir : Path
        Target run directory.
    manifest : Dict
        Manifest dictionary to save.
    """
    save_json(manifest, run_dir / "manifest.json")


def ensure_tables_dir(run_dir: Path) -> Path:
    """Ensure the tables directory exists within the run directory.

    Parameters
    ----------
    run_dir : Path
        The run directory.

    Returns
    -------
    Path
        Path to the tables directory.
    """
    d = run_dir / "tables"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _quantiles(x: np.ndarray, qs=(0.01, 0.05, 0.50, 0.95, 0.99)) -> dict[str, float]:
    """Compute specific quantiles for a numeric array, handling NaNs.

    Parameters
    ----------
    x : np.ndarray
        Input numeric array.
    qs : tuple of float
        Quantiles to compute (0.0 to 1.0).

    Returns
    -------
    dict[str, float]
        Dictionary mapping quantile keys (e.g., 'q01') to values.
    """
    x = x[np.isfinite(x)]
    if x.size == 0:
        return {f"q{int(q * 100):02d}": float("nan") for q in qs}
    out = {}
    for q in qs:
        out[f"q{int(q * 100):02d}"] = float(np.quantile(x, q))
    return out


def _safe_kurtosis(x: np.ndarray) -> float:
    """Compute Pearson's kurtosis robust to small sample sizes or zero variance.

    Parameters
    ----------
    x : np.ndarray
        Input numeric array.

    Returns
    -------
    float
        Kurtosis value, or NaN if sample size < 4 or variance is zero.
    """
    x = x[np.isfinite(x)]
    if x.size < 4:
        return float("nan")
    m = x.mean()
    v = np.mean((x - m) ** 2)
    if v <= 0:
        return float("nan")
    k = np.mean((x - m) ** 4) / (v**2)
    return float(k)


def _to_utc_dt(series_like) -> pd.Series:
    """Convert a series-like object to UTC datetime.

    Parameters
    ----------
    series_like : pd.Series or array-like
        Input data containing datetime-like values.

    Returns
    -------
    pd.Series
        Pandas Series converted to UTC datetime.
    """
    return pd.to_datetime(series_like, utc=True, errors="coerce")


def find_artifact(manifest: dict, prefix: str, suffix: str) -> str | None:
    """Locate a specific artifact file within the manifest data list.

    Parameters
    ----------
    manifest : dict
        Run manifest.
    prefix : str
        Filename prefix.
    suffix : str
        Filename suffix (extension).

    Returns
    -------
    str | None
        Relative path to the artifact if found, else None.
    """
    for f in manifest.get("artifacts", {}).get("data", []) or []:
        if f.startswith(prefix) and f.endswith(suffix):
            return f
    return None


def summarize_ohlcv(df: pd.DataFrame) -> dict[str, object]:
    """Compute descriptive statistics for OHLCV data.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing OHLCV data.

    Returns
    -------
    dict[str, object]
        Dictionary of descriptive statistics.

    Notes
    -----
    Descriptive only; no causal claims. Includes log-return moments and quantiles.
    """
    # Expect at least: ts, close; dt_utc may be string.
    dt_series = (
        _to_utc_dt(df["dt_utc"])
        if "dt_utc" in df.columns
        else _to_utc_dt(
            df["ts"],
        )
    )
    close = pd.to_numeric(df["close"], errors="coerce")

    logret = np.log(close).diff().to_numpy()
    logret = logret[np.isfinite(logret)]

    out = {
        "rows": int(len(df)),
        "start_utc": str(dt_series.min()),
        "end_utc": str(dt_series.max()),
        "columns": list(df.columns),
        "missing_rate_close": float(close.isna().mean()),
        "logret_mean": float(np.mean(logret)) if logret.size else float("nan"),
        "logret_std": float(np.std(logret)) if logret.size else float("nan"),
        "logret_kurtosis": _safe_kurtosis(logret),
        **{f"logret_{k}": v for k, v in _quantiles(logret).items()},
    }
    return out


def summarize_trades(df: pd.DataFrame) -> dict[str, object]:
    """Compute descriptive statistics for trade data.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing trade data.

    Returns
    -------
    dict[str, object]
        Dictionary of descriptive statistics.

    Notes
    -----
    Descriptive only. Inter-arrival is computed from timestamps (seconds).
    Intensity is aggregated as trades per minute (proxy of λ(t)).
    """
    dt_series = _to_utc_dt(df["dt_utc"]) if "dt_utc" in df.columns else _to_utc_dt(df["ts"])
    ts = pd.to_numeric(df["ts"], errors="coerce")

    # inter-arrival in seconds
    inter = (ts.diff() / 1000.0).to_numpy()
    inter = inter[np.isfinite(inter)]
    inter = inter[inter > 0]

    # intensity proxy: trades/min
    step_ms = 60_000
    bar_ts = (ts // step_ms) * step_ms
    intensity = (
        pd.DataFrame({"bar_ts": bar_ts})
        .dropna()
        .astype({"bar_ts": "int64"})
        .groupby("bar_ts")
        .size()
        .to_numpy()
    )

    out = {
        "rows": int(len(df)),
        "start_utc": str(dt_series.min()),
        "end_utc": str(dt_series.max()),
        "columns": list(df.columns),
        "missing_rate_ts": float(ts.isna().mean()),
        "interarrival_count": int(inter.size),
        "interarrival_mean_s": float(np.mean(inter)) if inter.size else float("nan"),
        "interarrival_std_s": float(np.std(inter)) if inter.size else float("nan"),
        **{f"interarrival_s_{k}": v for k, v in _quantiles(inter).items()},
        "intensity_bars": int(intensity.size),
        "intensity_mean_trades_per_min": (
            float(np.mean(intensity)) if intensity.size else float("nan")
        ),
        "intensity_max_trades_per_min": (
            float(np.max(intensity)) if intensity.size else float("nan")
        ),
        **{f"intensity_{k}": v for k, v in _quantiles(intensity.astype(float)).items()},
    }
    return out


def to_markdown_table(rows: list[tuple[str, object]]) -> str:
    """Render a list of key-value pairs as a Markdown table.

    Parameters
    ----------
    rows : list[tuple[str, object]]
        List of (key, value) tuples.

    Returns
    -------
    str
        Formatted Markdown table string.
    """
    # simple 2-col table
    lines = ["| Campo | Valor |", "|---|---|"]
    for k, v in rows:
        lines.append(f"| `{k}` | {v} |")
    return "\n".join(lines) + "\n"


def main():
    """Execute the data summary pipeline to generate descriptive tables."""
    ap = argparse.ArgumentParser(description="Generate Phase 1 data summary tables for a run.")
    ap.add_argument("--run_id", required=True, type=str)
    args = ap.parse_args()

    run_dir = Path("runs") / args.run_id
    if not run_dir.exists():
        raise SystemExit(f"Run directory not found: {run_dir}")

    manifest = load_manifest(run_dir)
    tables_dir = ensure_tables_dir(run_dir)

    # Locate data artifacts from manifest
    ohlcv_rel = find_artifact(manifest, "ohlcv_", ".parquet")
    trades_rel = find_artifact(manifest, "trades_", ".parquet")

    if not ohlcv_rel:
        raise SystemExit("Missing OHLCV parquet in manifest artifacts.data.")
    ohlcv_path = run_dir / ohlcv_rel

    # Load data
    try:
        ohlcv = pd.read_parquet(ohlcv_path).sort_values("ts").reset_index(drop=True)
    except Exception as e:
        raise SystemExit(f"Failed to read OHLCV parquet: {ohlcv_path} :: {e}") from e

    ohlcv_sum = summarize_ohlcv(ohlcv)

    trades_sum = None
    if trades_rel:
        trades_path = run_dir / trades_rel
        try:
            trades = pd.read_parquet(trades_path).sort_values("ts").reset_index(drop=True)
            trades_sum = summarize_trades(trades)
        except Exception as e:
            raise SystemExit(f"Failed to read trades parquet: {trades_path} :: {e}") from e

    # Build unified summary
    repo_url = (
        manifest.get("repository")
        or (manifest.get("git", {}) or {}).get("repository_url")
        or "unknown"
    )

    summary = {
        "generated_utc": utcnow_iso(),
        "run_id": args.run_id,
        "repository": repo_url,
        "phase": 1,
        "ohlcv": ohlcv_sum,
        "trades": trades_sum,
        "notes": [
            "Phase 1 uses public observables only (OHLCV + trades).",
            "All statistics are descriptive; no causal claims are made.",
            "Little’s Law variables (L, λ, W) are treated as proxy-inspiration; "
            "direct OMS/infra telemetry is out of scope.",
        ],
    }

    # Write JSON
    out_json = tables_dir / "data_summary.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write CSV (flattened key-value)
    flat_rows: list[tuple[str, object]] = [
        ("run_id", args.run_id),
        ("generated_utc", summary["generated_utc"]),
        ("repository", repo_url),
    ]
    for k, v in ohlcv_sum.items():
        flat_rows.append((f"ohlcv.{k}", v))
    if trades_sum:
        for k, v in trades_sum.items():
            flat_rows.append((f"trades.{k}", v))

    out_csv = tables_dir / "data_summary.csv"
    pd.DataFrame(flat_rows, columns=["field", "value"]).to_csv(out_csv, index=False)

    # Write Markdown (Methods-ready)
    md_parts = []
    md_parts.append("# Data Summary — Phase 1\n")
    md_parts.append(f"- **run_id:** `{args.run_id}`\n")
    md_parts.append(f"- **generated_utc:** `{summary['generated_utc']}`\n")
    md_parts.append(f"- **repository:** `{repo_url}`\n")
    md_parts.append("\n## OHLCV (1m)\n")
    md_parts.append(to_markdown_table([(k, ohlcv_sum[k]) for k in sorted(ohlcv_sum.keys())]))
    if trades_sum:
        md_parts.append("\n## Trades\n")
        md_parts.append(to_markdown_table([(k, trades_sum[k]) for k in sorted(trades_sum.keys())]))
    md_parts.append("\n## Notes\n")
    for n in summary["notes"]:
        md_parts.append(f"- {n}\n")

    out_md = tables_dir / "data_summary.md"
    out_md.write_text("".join(md_parts), encoding="utf-8")

    # Update manifest artifacts.tables
    manifest.setdefault("artifacts", {})
    manifest["artifacts"].setdefault("tables", [])
    tables_list = manifest["artifacts"]["tables"]

    for rel in ["tables/data_summary.md", "tables/data_summary.csv", "tables/data_summary.json"]:
        if rel not in tables_list:
            tables_list.append(rel)

    manifest.setdefault("parameters", {})
    manifest["parameters"]["data_summary"] = {
        "generated_utc": summary["generated_utc"],
        "tables": ["data_summary.md", "data_summary.csv", "data_summary.json"],
    }

    update_manifest(run_dir, manifest)

    # Update checksums
    files_to_hash: list[Path] = [run_dir / "manifest.json"]

    # include all referenced artifacts (data/figures/logs/tables)
    for f in manifest["artifacts"].get("data", []) or []:
        files_to_hash.append(run_dir / f)

    for f in manifest["artifacts"].get("figures", []) or []:
        files_to_hash.append(run_dir / "figures" / f)

    for f in manifest["artifacts"].get("logs", []) or []:
        p = run_dir / f
        if p.exists():
            files_to_hash.append(p)

    for f in manifest["artifacts"].get("tables", []) or []:
        files_to_hash.append(run_dir / f)

    checksum_path = run_dir / "checksums.sha256"
    write_checksums_sha256(files_to_hash, checksum_path)

    print("[OK] Data summary generated.")
    print(f"[OK] Wrote: {out_md}")
    print(f"[OK] Wrote: {out_csv}")
    print(f"[OK] Wrote: {out_json}")
    print("[OK] Manifest and checksums updated.")


if __name__ == "__main__":
    main()
