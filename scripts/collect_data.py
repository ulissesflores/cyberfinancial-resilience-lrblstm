"""Audit-grade market data collection for Phase 1 (public data).

Scientific design principles:
- Explicit, justified data sources (exchange, symbol, time window).
- Deterministic, well-defined time boundaries (UTC).
- Rate-limit aware collection.
- Run-based artifact management:
    - writes data artifacts into runs/<run_id>/
    - updates manifest.json
    - produces checksums.sha256

Collected data layers (Phase 1):
1) OHLCV (primary layer) for regime identification (volatility, drawdowns).
2) Trades (optional, API-limited) for throughput intensity (λ proxy) and inter-arrival analysis.

Note:
This Phase 1 dataset uses proxies for queue variables when system telemetry is not available.
Phase 2 will add direct queue observability (L, λ, W) from OMS/infra logs.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import time
from pathlib import Path
from typing import Any

import ccxt
import numpy as np
import pandas as pd
from hash_utils import save_json, write_checksums_sha256
from tqdm import tqdm

# -----------------------------
# Helpers
# -----------------------------


def utc_ms(ts: dt.datetime) -> int:
    """Convert a UTC-aware datetime object to Unix epoch milliseconds.

    Parameters
    ----------
    ts:
        Timezone-aware datetime (expected UTC).

    Returns
    -------
    int
        Unix epoch timestamp in milliseconds.
    """
    return int(ts.timestamp() * 1000)


def iso_utc_from_ms(ms: int) -> str:
    """Convert Unix epoch milliseconds to an ISO-8601 UTC timestamp string.

    Parameters
    ----------
    ms : int
        Unix epoch timestamp in milliseconds.

    Returns
    -------
    str
        ISO-8601 formatted UTC timestamp.
    """
    return dt.datetime.fromtimestamp(ms / 1000, tz=dt.UTC).isoformat()


def load_manifest(run_dir: Path) -> dict[str, Any]:
    """Load the run manifest from the specified directory.

    Parameters
    ----------
    run_dir : Path
        Directory containing the `manifest.json`.

    Returns
    -------
    dict[str, Any]
        Parsed manifest dictionary.
    """
    path = run_dir / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def update_manifest(run_dir: Path, manifest: dict[str, Any]) -> None:
    """Persist the updated manifest to the run directory."""
    save_json(manifest, run_dir / "manifest.json")


def get_exchange(name: str) -> Any:
    """Initialize a CCXT exchange instance with rate limiting enabled.

    Raises
    ------
    SystemExit
        If the exchange is not supported by ccxt.
    """
    ex_class = getattr(ccxt, name, None)
    if ex_class is None:
        raise SystemExit(f"Exchange not supported by ccxt: {name}")
    return ex_class({"enableRateLimit": True})


# -----------------------------
# OHLCV collection
# -----------------------------


def fetch_ohlcv_all(
    ex: Any,
    symbol: str,
    timeframe: str,
    since_ms: int,
    until_ms: int,
    limit: int = 1000,
    sleep_s: float = 0.2,
) -> pd.DataFrame:
    """Collect OHLCV data in batches.

    Parameters
    ----------
    ex : Any
        CCXT exchange instance.
    symbol : str
        Trading symbol (e.g., 'BTC/USDT').
    timeframe : str
        Candle timeframe (e.g., '1m').
    since_ms : int
        Start timestamp in milliseconds.
    until_ms : int
        End timestamp in milliseconds.
    limit : int, default=1000
        Pagination limit.
    sleep_s : float, default=0.2
        Sleep duration between requests in seconds.

    Returns
    -------
    pd.DataFrame
        DataFrame containing OHLCV data.

    Notes
    -----
    OHLCV defines regimes (volatility / drawdowns / trend changes).
    Since/until boundaries are explicit in UTC.
    Data is de-duplicated and ordered by timestamp.
    """
    rows: list[list[Any]] = []
    cursor = since_ms

    pbar = tqdm(desc="OHLCV", unit="batch")
    while cursor < until_ms:
        batch = ex.fetch_ohlcv(symbol, timeframe=timeframe, since=cursor, limit=limit)
        if not batch:
            break
        rows.extend(batch)

        last_ts = int(batch[-1][0])
        if last_ts <= cursor:
            cursor += 60_000
        else:
            cursor = last_ts + 1

        pbar.update(1)
        time.sleep(sleep_s)

        if last_ts >= until_ms:
            break

    pbar.close()

    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    df = df.drop_duplicates(subset=["ts"]).sort_values("ts").reset_index(drop=True)
    df["dt_utc"] = df["ts"].apply(iso_utc_from_ms)
    return df


# -----------------------------
# Trades collection (optional)
# -----------------------------


def fetch_trades_all(
    ex: Any,
    symbol: str,
    since_ms: int,
    until_ms: int,
    limit: int = 1000,
    sleep_s: float = 0.2,
    max_rows: int = 200_000,
) -> pd.DataFrame:
    """Collect trade data (API-limited on many exchanges).

    Parameters
    ----------
    ex : Any
        CCXT exchange instance.
    symbol : str
        Trading symbol.
    since_ms : int
        Start timestamp in milliseconds.
    until_ms : int
        End timestamp in milliseconds.
    limit : int, default=1000
        Pagination limit.
    sleep_s : float, default=0.2
        Sleep duration between requests.
    max_rows : int, default=200_000
        Maximum number of trades to collect.

    Returns
    -------
    pd.DataFrame
        DataFrame containing trade data.

    Notes
    -----
    Trades provide λ proxy (arrival intensity).
    Inter-arrival distributions can be heavy-tailed.
    Many exchanges limit historical depth; limitations are recorded in the manifest.
    """
    rows: list[dict[str, Any]] = []
    cursor = since_ms

    pbar = tqdm(desc="TRADES", unit="batch")
    while cursor < until_ms and len(rows) < max_rows:
        batch = ex.fetch_trades(symbol, since=cursor, limit=limit)
        if not batch:
            break

        for t in batch:
            ts = t.get("timestamp")
            if ts is None:
                continue
            ts = int(ts)
            if ts > until_ms:
                continue
            rows.append(
                {
                    "ts": ts,
                    "price": float(t.get("price", np.nan)),
                    "amount": float(t.get("amount", np.nan)),
                    "side": t.get("side"),
                    "trade_id": t.get("id"),
                }
            )

        last_ts = int(batch[-1]["timestamp"])
        cursor = last_ts + 1 if last_ts > cursor else cursor + 1

        pbar.update(1)
        time.sleep(sleep_s)

    pbar.close()

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.drop_duplicates(subset=["ts", "trade_id"]).sort_values("ts").reset_index(drop=True)
    df["dt_utc"] = df["ts"].apply(iso_utc_from_ms)
    return df


# -----------------------------
# Main
# -----------------------------


def main():
    """Execute the data collection pipeline for Phase 1 public market data."""
    ap = argparse.ArgumentParser(
        description="Collect Phase 1 public market data into a run directory."
    )
    ap.add_argument(
        "--run_id", type=str, required=True, help="Existing run_id under runs/<run_id>/"
    )
    ap.add_argument("--exchange", type=str, default="binance")
    ap.add_argument("--symbol", type=str, default="BTC/USDT")
    ap.add_argument("--timeframe", type=str, default="1m", choices=["1m", "5m", "15m", "1h"])
    ap.add_argument("--ohlcv_days", type=int, default=90)
    ap.add_argument("--with_trades", action="store_true")
    ap.add_argument("--trades_days", type=int, default=14)
    ap.add_argument("--max_trades", type=int, default=200_000)
    ap.add_argument("--sleep_s", type=float, default=0.2)
    args = ap.parse_args()

    run_dir = Path("runs") / args.run_id
    if not run_dir.exists():
        raise SystemExit(f"Run directory not found: {run_dir}")

    manifest = load_manifest(run_dir)

    ex = get_exchange(args.exchange)

    now = dt.datetime.now(dt.UTC)
    ohlcv_since = now - dt.timedelta(days=int(args.ohlcv_days))
    ohlcv_since_ms = utc_ms(ohlcv_since)
    now_ms = utc_ms(now)

    # Collect OHLCV
    ohlcv = fetch_ohlcv_all(
        ex,
        args.symbol,
        args.timeframe,
        since_ms=ohlcv_since_ms,
        until_ms=now_ms,
        sleep_s=float(args.sleep_s),
    )
    ohlcv_path = (
        run_dir / f"ohlcv_{args.exchange}_{args.symbol.replace('/', '-')}_{args.timeframe}.parquet"
    )
    ohlcv.to_parquet(ohlcv_path, index=False)

    # Collect trades (optional)
    trades_path: Path | None = None
    trades_rows = 0
    trades_window = None

    if args.with_trades:
        trades_since = now - dt.timedelta(days=int(args.trades_days))
        trades_since_ms = utc_ms(trades_since)
        trades = fetch_trades_all(
            ex,
            args.symbol,
            since_ms=trades_since_ms,
            until_ms=now_ms,
            max_rows=int(args.max_trades),
            sleep_s=float(args.sleep_s),
        )
        trades_path = run_dir / f"trades_{args.exchange}_{args.symbol.replace('/', '-')}.parquet"
        trades.to_parquet(trades_path, index=False)
        trades_rows = int(len(trades))
        trades_window = {
            "since_utc": trades_since.isoformat(),
            "until_utc": now.isoformat(),
            "max_trades": int(args.max_trades),
        }

    # Update manifest parameters + artifacts
    manifest["parameters"]["data_collection"] = {
        "exchange": args.exchange,
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "ohlcv_window": {
            "since_utc": ohlcv_since.isoformat(),
            "until_utc": now.isoformat(),
            "days": int(args.ohlcv_days),
        },
        "trades": {
            "enabled": bool(args.with_trades),
            "window": trades_window,
            "rows": trades_rows,
            "note": "Trades depth may be limited by exchange API policies.",
        },
        "sleep_s": float(args.sleep_s),
    }

    # Artifacts list (relative)
    manifest["artifacts"]["data"] = [ohlcv_path.name] + ([trades_path.name] if trades_path else [])
    manifest["artifacts"]["logs"].append("collect_data.log")

    # Write a minimal log (audit trail)
    log_lines = [
        f"run_id={args.run_id}",
        f"exchange={args.exchange}",
        f"symbol={args.symbol}",
        f"timeframe={args.timeframe}",
        f"ohlcv_rows={len(ohlcv)}",
        f"trades_enabled={bool(args.with_trades)}",
        f"trades_rows={trades_rows}",
        f"created_utc={now.isoformat()}",
    ]
    (run_dir / "collect_data.log").write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    # Checksums
    files_to_hash = [ohlcv_path, run_dir / "manifest.json", run_dir / "collect_data.log"]
    if trades_path:
        files_to_hash.append(trades_path)

    # Persist manifest (BEFORE checksums to ensure manifest.json on disk is final)
    update_manifest(run_dir, manifest)

    checksum_path = run_dir / "checksums.sha256"
    write_checksums_sha256(files_to_hash, checksum_path)

    print("[OK] Data collection complete.")
    print(f"[OK] OHLCV: {ohlcv_path.name} rows={len(ohlcv)}")
    if trades_path:
        print(f"[OK] Trades: {trades_path.name} rows={trades_rows}")
    print(f"[OK] Checksums: {checksum_path.name}")
    print("[OK] Manifest updated: manifest.json")


if __name__ == "__main__":
    main()
