"""Audit-grade EDA for Phase 1 dataset (publish-grade figures).

Scientific objectives (minimum publishable EDA):
1) Regime diagnostics (volatility clustering, drawdowns).
2) Throughput intensity proxies (trade_count/min) from trades (proxy of λ(t)).
3) Inter-arrival heavy-tail diagnostics (trades).

Outputs (run contract):
- Figures saved under runs/<run_id>/figures/
- manifest.json updated (artifacts.figures + parameters.eda)
- checksums.sha256 updated to include data + figures + manifest + logs

Important scope note:
Phase 1 uses public market proxies (OHLCV + trades). It does NOT claim direct
observability of Little variables (L, λ, W) inside OMS/infra. That comes in Phase 2.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import textwrap
import time
from collections.abc import Iterable
from pathlib import Path

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from hash_utils import save_json, write_checksums_sha256

matplotlib.use("Agg")

# -----------------------------
# IO + logging
# -----------------------------


def utc_now_iso() -> str:
    """Return current UTC time as an ISO-8601 string without microseconds (Z suffix).

    Returns
    -------
    str
        ISO-8601 formatted UTC timestamp.
    """
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def log(msg: str, log_path: Path | None = None) -> None:
    """Log a timestamped message to stdout and optionally append it to a file.

    Parameters
    ----------
    msg : str
        Message to log.
    log_path : Path | None, optional
        Path to the log file.
    """
    line = f"[{utc_now_iso()}] {msg}"
    print(line, flush=True)
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def step(msg: str, log_path: Path | None = None) -> float:
    """Log a step marker and return a perf counter timestamp for duration measurement.

    Parameters
    ----------
    msg : str
        Step description.
    log_path : Path | None, optional
        Path to the log file.

    Returns
    -------
    float
        Current performance counter value.
    """
    log(f"STEP -> {msg}", log_path=log_path)
    return time.perf_counter()


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
    manifest : dict
        Manifest dictionary to save.
    """
    save_json(manifest, run_dir / "manifest.json")


def ensure_figdir(run_dir: Path) -> Path:
    """Ensure the figures directory exists within the run directory.

    Parameters
    ----------
    run_dir : Path
        The run directory.

    Returns
    -------
    Path
        Path to the figures directory.
    """
    figdir = run_dir / "figures"
    figdir.mkdir(parents=True, exist_ok=True)
    return figdir


# -----------------------------
# Math
# -----------------------------


def realized_vol(close: pd.Series, window: int) -> pd.Series:
    """Compute realized volatility as the rolling standard deviation of log returns.

    Parameters
    ----------
    close : pd.Series
        Time series of close prices.
    window : int
        Rolling window size.

    Returns
    -------
    pd.Series
        Realized volatility series scaled by sqrt(window).

    Notes
    -----
    Used as a regime proxy. Descriptive only; no causal claims.
    """
    r = np.log(close).diff()
    return r.rolling(window).std() * np.sqrt(window)


# -----------------------------
# Plot styling (publish-grade)
# -----------------------------


def _format_datetime_axis(ax: plt.Axes) -> None:
    """Apply concise date formatting to the x-axis.

    Parameters
    ----------
    ax : plt.Axes
        Matplotlib axes object to format.
    """
    locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    # Publicável: sem rotação agressiva, evita “borrão”
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")


def _apply_common_style(ax: plt.Axes) -> None:
    """Apply consistent grid and spine styling to a plot axes.

    Parameters
    ----------
    ax : plt.Axes
        Matplotlib axes object to style.
    """
    ax.grid(True, alpha=0.25)
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)


def _build_footer_lines(
    run_id: str,
    repo_url: str,
    author: str,
    project_title: str,
    data_scope: str,
) -> list[str]:
    """Construct and wrap the provenance footer text.

    Parameters
    ----------
    run_id : str
        Unique identifier for the run.
    repo_url : str
        URL of the repository.
    author : str
        Author name.
    project_title : str
        Title of the project.
    data_scope : str
        Description of the data scope.

    Returns
    -------
    list[str]
        List of strings representing the wrapped footer text.
    """
    # Conteúdo “proveniência” (auditável) — texto longo por natureza.
    # Vamos quebrar em múltiplas linhas de forma controlada.
    footer = f"run_id={run_id} | {data_scope} | repo={repo_url} | author={author} | {project_title}"
    # Quebra agressiva o suficiente para caber bem em 3–4 linhas em A4/16:9.
    wrapped = textwrap.wrap(footer, width=110, break_long_words=False, break_on_hyphens=False)
    # Garante ao menos 2 linhas (estética) e no máximo 4 (não roubar área do gráfico)
    if len(wrapped) == 1:
        wrapped = [wrapped[0], ""]
    return wrapped[:4]


def _add_footer(fig: plt.Figure, lines: Iterable[str]) -> int:
    """Render the footer text onto the figure canvas.

    Parameters
    ----------
    fig : plt.Figure
        Matplotlib figure object.
    lines : Iterable[str]
        Lines of text to render.

    Returns
    -------
    int
        Number of lines actually rendered.
    """
    # Remove linhas vazias no final, mas preserva formatação geral
    lines = [ln for ln in list(lines) if ln is not None]
    while lines and lines[-1] == "":
        lines.pop()

    n = max(1, len(lines))
    footer_text = "\n".join(lines)

    # Posição: canto inferior esquerdo (fig coords).
    # Importante: NÃO chamar fig.text múltiplas vezes com o mesmo conteúdo.
    fig.text(
        0.01,
        0.01,
        footer_text,
        ha="left",
        va="bottom",
        fontsize=8,
        alpha=0.9,
        family="sans-serif",
    )
    return n


def _compute_bottom_margin(n_footer_lines: int) -> float:
    """Calculate the bottom margin required to fit the footer.

    Parameters
    ----------
    n_footer_lines : int
        Number of lines in the footer.

    Returns
    -------
    float
        Bottom margin as a fraction of the figure height.
    """
    # Margem inferior em fração do canvas.
    # Ajuste pragmático para 8pt footer e 1–4 linhas.
    # 1 linha ~ 0.10; 2 linhas ~ 0.13; 3 linhas ~ 0.16; 4 linhas ~ 0.19
    return min(0.10 + 0.03 * (n_footer_lines - 1), 0.21)


def save_figure(fig: plt.Figure, out_path: Path, footer_lines: list[str], dpi: int = 220) -> None:
    """Save a Matplotlib figure with provenance metadata and publication-grade formatting.

    Parameters
    ----------
    fig : plt.Figure
        Matplotlib figure object.
    out_path : Path
        Destination path.
    footer_lines : list[str]
        Lines of text for the provenance footer.
    dpi : int, default=220
        Resolution for the output image.
    """
    n_lines = _add_footer(fig, footer_lines)
    bottom = _compute_bottom_margin(n_lines)
    fig.subplots_adjust(bottom=bottom)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_series_datetime(
    x_dt: pd.Series,
    y: np.ndarray,
    title: str,
    out_path: Path,
    footer_lines: list[str],
    xlabel: str = "",
    ylabel: str = "",
) -> None:
    """Plot a time series with UTC datetime axis formatting and provenance footer.

    Parameters
    ----------
    x_dt : pd.Series
        Datetime series (UTC).
    y : np.ndarray
        Values to plot.
    title : str
        Figure title.
    out_path : Path
        Output file path.
    footer_lines : list[str]
        Provenance metadata.
    xlabel : str, optional
        X-axis label.
    ylabel : str, optional
        Y-axis label.
    """
    x = pd.to_datetime(x_dt, utc=True, errors="coerce")
    if x.isna().all():
        x_plot = np.arange(len(y))
    else:
        x_plot = x

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(x_plot, y, linewidth=1.2)
    ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)

    if not x.isna().all():
        _format_datetime_axis(ax)

    _apply_common_style(ax)
    fig.tight_layout()
    save_figure(fig, out_path, footer_lines=footer_lines, dpi=220)


def plot_hist(
    values: np.ndarray,
    title: str,
    out_path: Path,
    footer_lines: list[str],
    bins: int = 120,
    logy: bool = False,
    xlabel: str = "",
    ylabel: str = "",
) -> None:
    """Plot a histogram with optional log-scale y-axis and provenance footer.

    Parameters
    ----------
    values : np.ndarray
        Data array.
    title : str
        Figure title.
    out_path : Path
        Output file path.
    footer_lines : list[str]
        Provenance metadata.
    bins : int, default=120
        Number of histogram bins.
    logy : bool, default=False
        If True, use log scale for y-axis.
    xlabel : str, optional
        X-axis label.
    ylabel : str, optional
        Y-axis label.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.hist(values, bins=bins)
    ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if logy:
        ax.set_yscale("log")

    _apply_common_style(ax)
    fig.tight_layout()
    save_figure(fig, out_path, footer_lines=footer_lines, dpi=220)


# -----------------------------
# Main
# -----------------------------


def main() -> None:
    """Execute the EDA pipeline to generate publication-grade figures."""
    ap = argparse.ArgumentParser(description="Generate publish-grade EDA figures for a run.")
    ap.add_argument("--run_id", type=str, required=True)
    args = ap.parse_args()

    run_dir = Path("runs") / args.run_id
    if not run_dir.exists():
        raise SystemExit(f"Run directory not found: {run_dir}")

    figdir = ensure_figdir(run_dir)
    manifest = load_manifest(run_dir)

    # Canonical log for this script (artifact)
    eda_log_path = run_dir / "eda_generate_figures.log"

    log("EDA started", log_path=eda_log_path)
    log(f"Using run_id={args.run_id}", log_path=eda_log_path)

    data_files: list[str] = manifest.get("artifacts", {}).get("data", [])
    if not data_files:
        raise SystemExit("No data artifacts recorded in manifest. Run collect_data.py first.")

    ohlcv_candidates = [f for f in data_files if f.startswith("ohlcv_") and f.endswith(".parquet")]
    trades_candidates = [
        f for f in data_files if f.startswith("trades_") and f.endswith(".parquet")
    ]

    if not ohlcv_candidates:
        raise SystemExit("Missing OHLCV parquet in artifacts.data.")

    ohlcv_path = run_dir / ohlcv_candidates[0]

    # Footer metadata (proveniência)
    repo_url = (
        manifest.get("repository")
        or (manifest.get("git", {}) or {}).get("repository_url")
        or "unknown"
    )
    author = "Carlos Ulisses Flores"
    project_title = "Cyber-Financial Resilience via Little’s Law + Bayesian LSTM (LR-BLSTM)"
    data_scope = "Binance public market data (OHLCV + Trades)"

    footer_lines = _build_footer_lines(
        run_id=args.run_id,
        repo_url=repo_url,
        author=author,
        project_title=project_title,
        data_scope=data_scope,
    )

    # Load OHLCV
    t = step("Loading OHLCV parquet", log_path=eda_log_path)
    ohlcv = pd.read_parquet(ohlcv_path).sort_values("ts").reset_index(drop=True)
    log(f"OHLCV loaded: rows={len(ohlcv)} in {time.perf_counter() - t:.2f}s", log_path=eda_log_path)

    # Compute features
    t = step("Computing returns, drawdown, realized volatility", log_path=eda_log_path)
    ohlcv["ret"] = np.log(ohlcv["close"]).diff()
    ohlcv["cumret"] = ohlcv["ret"].fillna(0).cumsum()
    ohlcv["drawdown"] = ohlcv["cumret"] - ohlcv["cumret"].cummax()
    ohlcv["rv_30"] = realized_vol(ohlcv["close"], 30)
    ohlcv["rv_120"] = realized_vol(ohlcv["close"], 120)
    log(f"Features computed in {time.perf_counter() - t:.2f}s", log_path=eda_log_path)

    figures: list[str] = []

    # 01 Close
    f1 = figdir / "01_close.png"
    t = step("Saving figure 01_close.png", log_path=eda_log_path)
    plot_series_datetime(
        x_dt=ohlcv["dt_utc"],
        y=ohlcv["close"].to_numpy(),
        title="Close (BTC/USDT) — Phase 1",
        out_path=f1,
        footer_lines=footer_lines,
        xlabel="UTC",
        ylabel="Preço",
    )
    figures.append(f1.name)
    log(f"Saved 01_close.png in {time.perf_counter() - t:.2f}s", log_path=eda_log_path)

    # 02 Realized Vol
    f2 = figdir / "02_realized_vol.png"
    t = step("Saving figure 02_realized_vol.png", log_path=eda_log_path)

    x_dt = pd.to_datetime(ohlcv["dt_utc"], utc=True, errors="coerce")

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(x_dt, ohlcv["rv_30"], label="RV(30)", linewidth=1.1)
    ax.plot(x_dt, ohlcv["rv_120"], label="RV(120)", linewidth=1.1)
    ax.set_title("Realized Volatility (log-return std) — proxy de regime")
    ax.set_xlabel("UTC")
    ax.set_ylabel("Volatilidade (std)")
    ax.legend(loc="upper right", frameon=True)

    _format_datetime_axis(ax)
    _apply_common_style(ax)
    fig.tight_layout()
    save_figure(fig, f2, footer_lines=footer_lines, dpi=220)

    figures.append(f2.name)
    log(f"Saved 02_realized_vol.png in {time.perf_counter() - t:.2f}s", log_path=eda_log_path)

    # 03 Drawdown
    f3 = figdir / "03_drawdown.png"
    t = step("Saving figure 03_drawdown.png", log_path=eda_log_path)
    plot_series_datetime(
        x_dt=ohlcv["dt_utc"],
        y=ohlcv["drawdown"].to_numpy(),
        title="Log Drawdown — proxy de estresse",
        out_path=f3,
        footer_lines=footer_lines,
        xlabel="UTC",
        ylabel="Drawdown (log)",
    )
    figures.append(f3.name)
    log(f"Saved 03_drawdown.png in {time.perf_counter() - t:.2f}s", log_path=eda_log_path)

    # Trades (optional)
    if trades_candidates:
        trades_path = run_dir / trades_candidates[0]

        t = step("Loading trades parquet", log_path=eda_log_path)
        trades = pd.read_parquet(trades_path).sort_values("ts").reset_index(drop=True)
        log(
            f"Trades loaded: rows={len(trades)} in {time.perf_counter() - t:.2f}s",
            log_path=eda_log_path,
        )

        # Inter-arrival (s)
        inter = (trades["ts"].diff() / 1000.0).dropna()
        inter = inter[(inter > 0) & np.isfinite(inter)]

        f4 = figdir / "04_trade_interarrival_hist.png"
        t = step("Saving figure 04_trade_interarrival_hist.png", log_path=eda_log_path)
        plot_hist(
            values=inter.to_numpy(),
            title="Trade inter-arrival (s) — hist",
            out_path=f4,
            footer_lines=footer_lines,
            bins=140,
            logy=False,
            xlabel="Inter-arrival (s)",
            ylabel="count",
        )
        figures.append(f4.name)
        log(
            f"Saved 04_trade_interarrival_hist.png in {time.perf_counter() - t:.2f}s",
            log_path=eda_log_path,
        )

        f5 = figdir / "05_trade_interarrival_hist_logy.png"
        t = step("Saving figure 05_trade_interarrival_hist_logy.png", log_path=eda_log_path)
        plot_hist(
            values=inter.to_numpy(),
            title="Trade inter-arrival (s) — hist (log-y) diagnóstico de cauda",
            out_path=f5,
            footer_lines=footer_lines,
            bins=140,
            logy=True,
            xlabel="Inter-arrival (s)",
            ylabel="count (log)",
        )
        figures.append(f5.name)
        log(
            f"Saved 05_trade_interarrival_hist_logy.png in {time.perf_counter() - t:.2f}s",
            log_path=eda_log_path,
        )

        # Intensity: trades/min (λ proxy)
        step_ms = 60_000
        trades["bar_ts"] = (trades["ts"] // step_ms) * step_ms
        intensity = trades.groupby("bar_ts").size().rename("trade_count").reset_index()
        intensity["dt_utc"] = pd.to_datetime(intensity["bar_ts"], unit="ms", utc=True)

        f6 = figdir / "06_trade_intensity.png"
        t = step("Saving figure 06_trade_intensity.png", log_path=eda_log_path)
        plot_series_datetime(
            x_dt=intensity["dt_utc"],
            y=intensity["trade_count"].to_numpy(),
            title="Trade intensity (count/min) — proxy de λ(t)",
            out_path=f6,
            footer_lines=footer_lines,
            xlabel="UTC",
            ylabel="trades/min",
        )
        figures.append(f6.name)
        log(
            f"Saved 06_trade_intensity.png in {time.perf_counter() - t:.2f}s",
            log_path=eda_log_path,
        )

    # Update manifest + checksums
    t = step("Updating manifest and checksums", log_path=eda_log_path)

    manifest.setdefault("artifacts", {})
    manifest["artifacts"]["figures"] = figures

    # Ensure logs include canonical script log
    manifest["artifacts"].setdefault("logs", [])
    if "eda_generate_figures.log" not in manifest["artifacts"]["logs"]:
        manifest["artifacts"]["logs"].append("eda_generate_figures.log")

    manifest.setdefault("parameters", {})
    manifest["parameters"]["eda"] = {
        "generated_utc": dt.datetime.now(dt.UTC).isoformat(),
        "figures_count": len(figures),
        "notes": [
            "EDA Phase 1: proxies de regime (RV, drawdown), intensidade (trades/min) "
            "e caudas (inter-arrival).",
            "Sem alegações causais; observabilidade direta de Little (L, λ, W) "
            "requer telemetria (Phase 2).",
            "Figures are publish-grade: datetime axis + concise ticks + "
            "wrapped provenance footer (multi-line).",
        ],
    }

    update_manifest(run_dir, manifest)

    files_to_hash: list[Path] = [run_dir / "manifest.json"]
    for f in manifest["artifacts"].get("data", []):
        files_to_hash.append(run_dir / f)
    for f in figures:
        files_to_hash.append(figdir / f)
    for log_name in manifest["artifacts"].get("logs", []) or []:
        p = run_dir / log_name
        if p.exists():
            files_to_hash.append(p)

    checksum_path = run_dir / "checksums.sha256"
    write_checksums_sha256(files_to_hash, checksum_path)

    log(f"Checksums updated in {time.perf_counter() - t:.2f}s", log_path=eda_log_path)

    log("[OK] EDA complete.", log_path=eda_log_path)
    log(f"[OK] Figures generated: {len(figures)}", log_path=eda_log_path)
    log(f"[OK] Figures dir: {figdir}", log_path=eda_log_path)
    log("[OK] Manifest and checksums updated.", log_path=eda_log_path)
    log("EDA finished", log_path=eda_log_path)


if __name__ == "__main__":
    main()
