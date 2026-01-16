# Data Rationale (Phase 1) — Public Proxies for Cyber-Financial Resilience

## Premise
The system under analysis is a **socio-technical cyber-financial system** whose emergent behavior is partially observable via **public market metrics** (price and trades). Little's Law (L = λW) is treated as a **structural flow invariant**, but is **not directly observable** from public data.

## Evidence
1. **Crypto markets** exhibit heavy tails, regimes, and non-stationarity across multiple scales.
2. Public data available in a reproducible manner:
   - OHLCV at 1-minute (price regime proxy)
   - Trades (intensity/arrival and burstiness proxy)
3. The actual microstructure (deep order book, internal execution queues, OMS/infrastructure telemetry) is not fully exposed by public APIs.

## Critical Conclusion
In Phase 1, we adopt **observational proxies** to build an auditable empirical baseline:
- **Regime proxy:** realized volatility (RV) and logarithmic drawdown.
- **Arrival proxy:** trade inter-arrival distribution (indicative of tails and autocorrelation).
- **Intensity proxy (λ(t)):** trades/min as an arrival rate proxy.

There is no claim of causality nor direct measurement of (L, λ, W) from internal execution queues. These components will be addressed in later phases via **operational telemetry** or calibrated simulation.