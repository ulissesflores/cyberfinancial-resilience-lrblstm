# Cyber-Financial Resilience via Little’s Law and Bayesian LSTM (LR-BLSTM)

## 🇧🇷 Resumo (Português)

Este repositório apresenta um artefato científico reprodutível para análise de resiliência ciberfinanceira em mercados de criptoativos, utilizando dados públicos de alta frequência (OHLCV e trades) e proxies inspirados na Lei de Little. A Fase 1 concentra-se em Exploratory Data Analysis (EDA) rigoroso, com ênfase em regimes de mercado, estresse sistêmico e intensidade de fluxo, estabelecendo a base empírica para modelagem probabilística futura via Redes LSTM Bayesianas.

O objetivo científico central é investigar como invariantes de sistemas de filas (L, λ, W) podem ser operacionalizados como variáveis latentes observáveis por proxy em sistemas financeiros digitais, respeitando explicitamente limites epistemológicos (ausência de alegações causais diretas).

---

## 🇺🇸 Abstract (English)

This repository provides a fully reproducible scientific artifact for the analysis of cyber-financial resilience in crypto-asset markets using high-frequency public data (OHLCV and trades) and proxies inspired by Little’s Law. Phase 1 focuses on rigorous Exploratory Data Analysis (EDA), emphasizing market regimes, systemic stress, and flow intensity as empirical foundations for future probabilistic modeling via Bayesian LSTM networks.

The core scientific objective is to investigate how queueing-system invariants (L, λ, W) can be operationalized as proxy-observable latent variables in digital financial systems, while explicitly acknowledging epistemic and observability limits (no direct causal claims).

---

## 🇪🇸 Resumen (Español)

Este repositorio presenta un artefacto científico reproducible para el análisis de la resiliencia ciberfinanciera en mercados de criptoactivos, utilizando datos públicos de alta frecuencia (OHLCV y trades) y proxies inspirados en la Ley de Little. La Fase 1 se centra en un Análisis Exploratorio de Datos (EDA) riguroso, con énfasis en regímenes de mercado, estrés sistémico e intensidad de flujo, estableciendo la base empírica para una modelización probabilística futura mediante redes LSTM bayesianas.

El objetivo científico central es investigar cómo los invariantes de sistemas de colas (L, λ, W) pueden operacionalizarse como variables latentes observables por proxy en sistemas financieros digitales, respetando explícitamente los límites epistemológicos (sin afirmaciones causales directas).

---

## Scientific Motivation

Modern crypto-financial markets operate as complex socio-technical systems characterized by:
- Heavy-tailed distributions
- Regime switching and non-stationarity
- Burstiness and clustered volatility
- Structural breaks and stress propagation

Classical econometric assumptions often fail under these conditions. By integrating:
- Market microstructure observables,
- Queueing-theoretic intuition derived from Little’s Law,
- Probabilistic sequence models (Bayesian LSTM),

this project aims to advance the state of the art in cyber-financial resilience analysis, while preserving strict reproducibility and auditability.

---

## Repository Structure

```
cyberfinancial-resilience-lrblstm/
├── configs/              # Experiment and data configuration (YAML)
├── docs/                 # Scientific documentation (rationale, model card, threats)
├── schema/               # Formal data and manifest schemas
├── scripts/              # Reproducible pipelines (data collection, EDA, summaries)
├── runs/                 # Immutable experimental runs (data + artifacts)
├── notebooks/            # Optional exploratory notebooks (documentation-first)
├── outputs/              # Aggregated outputs and archives
├── README.md             # This document
├── CHANGELOG.md
├── LICENSE
├── CITATION.cff
└── requirements.txt
```

---

## Data Sources


- Exchange: Binance (public market data)
- Instruments: BTC/USDT
- Granularity: 1-minute OHLCV + individual trades
- Access Method: Public REST API

No private, proprietary, or user-identifiable data are used.

---

## Reproducibility Contract

This project follows a strict reproducibility contract:
1. Each experimental run is immutable and identified by `run_id`.
2. All artifacts (data, figures, logs) are checksummed (SHA-256).
3. A machine-readable `manifest.json` records parameters and outputs.
4. All figures are generated programmatically.

Any third party should be able to reproduce Phase 1 results by following the steps below.

---

## How to Reproduce (Phase 1)

### 1. Environment setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Data collection

```bash
python scripts/collect_data.py \
  --run_id <RUN_ID> \
  --exchange binance \
  --symbol BTC/USDT \
  --timeframe 1m \
  --ohlcv_days 90 \
  --with_trades \
  --trades_days 14
```

### 3. Generate EDA figures

```bash
python scripts/eda_generate_figures.py --run_id <RUN_ID>
```

All outputs will be stored under `runs/<RUN_ID>/`.

---

## Generated Artifacts (Phase 1)

- Price trajectory
- Realized volatility (multiple windows)
- Log drawdown (stress proxy)
- Trade inter-arrival distributions (linear and log-y)
- Trade intensity λ(t) proxy

These artifacts support descriptive, not causal, claims.

---

## Limitations

- Proxies inspired by Little’s Law are observational, not direct measurements.
- Exchange APIs provide partial visibility (no full order book depth here).
- Results are regime- and period-dependent.

All limitations are explicitly documented in `docs/threat_model.md`.

---

## License

This project is released under the Apache License 2.0, allowing academic and industrial reuse with attribution.

---

## How to Cite

If you use this work, please cite it as described in `CITATION.cff`.

---

## Author

**Carlos Ulisses Flores**
Independent Researcher — Cyber-Financial Resilience
CTO & Chief Researcher — Codex Hash Ltda. (Brazil)

---

## Project Status

- ✅ Phase 1 — Data pipeline and EDA (complete)
- ⏳ Phase 2 — Bayesian LSTM modeling (planned)
- ⏳ Phase 3 — Resilience metrics and stress propagation (planned)
