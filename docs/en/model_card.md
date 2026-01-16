# Model Card — LR-BLSTM (Phase 1 → Phase 2)

## Model (Overview)
**LR-BLSTM** (Little-Regularized Bayesian LSTM) is a modeling plan that combines:
- invariants/constraints inspired by Little's Law,
- sequential modeling (LSTM),
- uncertainty calibration (Bayesian deep learning).

## Current State (Phase 1)
**No model training yet.** Phase 1 produces:
- curated public dataset (OHLCV + trades),
- figures and regime diagnostics,
- arrival/intensity metrics.

## Prediction Objective (Phase 2)
Infer a latent state of "resilience" and/or instability (e.g., probability of stress regime), with calibrated uncertainty.

## Inputs (Phase 1 Observables)
- OHLCV 1m: open, high, low, close, volume
- Trades: timestamps (ms), price, amount (when available), side (when available)

## Outputs (Phase 1)
- EDA Figures (PNG)
- Data Summary Tables (MD/CSV/JSON)
- Manifest + checksums

## Future Metrics (Phase 2)
- Prediction error: MAE/RMSE
- Robustness and stress: splits by regime
- Calibration: ECE/CRPS
- Resilience metrics: recovery time (proxy), drawdown survival, throughput degradation (proxy)

## Limitations (Phase 1)
- Public proxies do not directly measure L, λ, W of internal queues.
- Public API may impose limits and truncations.
- Non-stationarity implies generalization risk.

## Responsible
Carlos Ulisses Flores — Codex Hash Ltda. (Brazil)