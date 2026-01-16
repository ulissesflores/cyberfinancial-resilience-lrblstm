# Threat Model & Threats to Validity (Phase 1)

## 1) Internal Validity Threats (Inference)
- **Spurious correlation:** proxies may correlate due to a common regime, not causality.
- **Non-stationarity / regime shifts:** patterns change; results depend on the selected time window.
- **Sampling/truncation:** trades may be limited by API or by the `max_trades` parameter.
- **Time alignment:** misalignments between OHLCV and trades can produce artifacts if aggregation is not consistent.

## 2) External Validity Threats (Generalization)
- **Exchange-specific:** Binance does not represent the entire ecosystem.
- **Instrument-specific:** BTC/USDT may differ from altcoins.
- **Market microstructure changes:** changes in fees, matching engine, liquidity.

## 3) Operational Threats (Reproducibility)
- Public API dependence (availability, rate limits).
- Library dependencies (e.g., `pyarrow`) vary by platform.
- Timezone/locale: mitigated by end-to-end UTC usage.

## 4) Adversarial Threats (when advancing to Phase 2)
- **Data poisoning:** pattern injection via wash trading (limited in Phase 1, but possible).
- **Adversarial concept drift:** deliberate changes in microstructure can "break" models.
- **Goodhart effects:** using prediction to control execution can feedback into the system.

## 5) Mitigations (Phase 1)
- Manifest + SHA-256 checksums.
- Immutable logs and `run_id`.
- Explicit declaration of proxies (no overclaims).
- Data Summary + formal schemas.

## 6) Falsification Criteria (Phase 1)
- If inter-arrival distributions do not exhibit heavy tails or clustering, the hypothesis of *burstiness* relevant to resilience must be reviewed.
- If λ(t) does not vary significantly, the utility of the intensity proxy may be marginal for the analyzed window.