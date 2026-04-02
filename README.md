# Cyber-Financial Resilience (LR-BLSTM)

Reproducible research software for studying cyber-financial resilience in crypto markets using high-frequency public data, Little's Law-inspired observability proxies, and a roadmap toward Bayesian sequence modeling.

This repository is designed as an audit-grade scientific artifact. Phase 1 is complete and focuses on data collection, exploratory analysis, and reproducible run management. Later phases extend the project toward Bayesian LSTM modeling and resilience-oriented inference under market stress and non-stationarity.

## At a glance

- Domain: cyber-financial resilience and public-market observability
- Data source: Binance public API
- Current artifact phase: Phase 1 baseline complete
- Latest release: [v0.1.1 — Citable Artifact & DOI Registration](https://github.com/ulissesflores/cyberfinancial-resilience-lrblstm/releases/tag/v0.1.1)
- DOI: [10.5281/zenodo.18275035](https://doi.org/10.5281/zenodo.18275035)
- Documentation: reproducibility notes, data rationale, threat model, and model card in `docs/`

## What this repository is

- a reproducible pipeline for collecting high-frequency public market data
- a run-based artifact system with manifests, checksums, and deterministic traceability
- an exploratory analysis layer for volatility, stress, and flow-intensity proxies
- the software foundation for future Bayesian LSTM work on cyber-financial resilience

## Why it matters

Crypto-financial markets behave like complex socio-technical systems:

- they are non-stationary
- they exhibit burstiness and clustered volatility
- they show regime shifts and stress propagation
- they offer only partial observability through public market data

This project uses queueing intuition inspired by Little's Law to construct proxy-observable signals while keeping strict epistemic guardrails: the outputs are descriptive and reproducible, not causal claims disguised as certainty.

## Current project status

- Phase 1: data pipeline and EDA complete
- Phase 2: Bayesian LSTM modeling planned
- Phase 3: resilience metrics and stress propagation planned

## Key outputs

- immutable run directories under `runs/<RUN_ID>/`
- machine-readable manifests and SHA-256 checksums
- generated figures for volatility, drawdowns, trade intensity, and inter-arrival behavior
- multilingual scientific documentation for reproducibility and modeling scope

## Data and observability

- Exchange: Binance public API
- Instrument: BTC/USDT
- Granularity: 1-minute OHLCV plus public trades
- Access model: public REST only

The repository does not use proprietary, private, or user-identifiable data.

## Quick reproduction

### 1. Create the environment

```bash
git clone https://github.com/ulissesflores/cyberfinancial-resilience-lrblstm.git
cd cyberfinancial-resilience-lrblstm

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Initialize a run

```bash
python scripts/make_run.py --note "phase-1 baseline"
```

Use the generated `run_id` printed by the script in the next steps.

### 3. Collect market data

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

### 4. Generate EDA outputs

```bash
python scripts/eda_generate_figures.py --run_id <RUN_ID>
```

All generated artifacts are written under `runs/<RUN_ID>/`.

## Scientific guardrails

- queue-inspired variables are proxy observables, not direct queue measurements
- public exchange APIs provide partial visibility
- results are period- and regime-dependent
- the repository makes descriptive and methodological claims, not direct causal claims

## Multilingual documentation

- [English reproducibility notes](./docs/en/reproducibility.md)
- [English data rationale](./docs/en/data_rationale.md)
- [English threat model](./docs/en/threat_model.md)
- [English model card](./docs/en/model_card.md)

Additional documentation is also available in `pt-BR` and `es`.

## Citation and release

- Citation metadata: [CITATION.cff](./CITATION.cff)
- Machine-readable metadata: [codemeta.json](./codemeta.json)
- Latest release: [v0.1.1 — Citable Artifact & DOI Registration](https://github.com/ulissesflores/cyberfinancial-resilience-lrblstm/releases/tag/v0.1.1)
- DOI: [10.5281/zenodo.18275035](https://doi.org/10.5281/zenodo.18275035)

If you use this work, cite the DOI-backed archival release rather than an unversioned repository snapshot.

## Repository layout

```text
configs/   run and data configuration
docs/      scientific documentation in multiple languages
schema/    formal schemas for datasets and manifests
scripts/   reproducible data collection and EDA pipelines
runs/      immutable run outputs created during execution
```
