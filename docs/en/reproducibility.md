# Reproducibility Statement

This document defines the reproducibility contract for the project **Cyber-Financial Resilience via Little’s Law and Bayesian LSTM**.

The objective is to ensure that all reported results, figures, and tables can be independently regenerated from raw public data, subject to clearly stated limitations.

---

## Scope

This reproducibility statement applies to **Phase 1** of the project, which includes:
- Public data collection (OHLCV and trades).
- Audit-grade Exploratory Data Analysis (EDA).
- Data summary tables used in the Methods/Data sections of the associated paper.

No claims of causal inference or infrastructure-level observability are made in this phase.

---

## Reproducible Units

The fundamental unit of reproducibility is a **run**, identified by a unique `run_id`.

Each run contains:
- Raw data artifacts (Parquet files).
- Generated figures and tables.
- Execution logs.
- A machine-readable `manifest.json`.
- Cryptographic checksums (`checksums.sha256`).

Once created, a run is treated as **immutable**.

---

## Deterministic Components

The following components are deterministic, conditional on identical inputs:
- Feature engineering and statistical computations.
- Figure generation code.
- Data summary tables.
- Manifest and checksum generation.

Given the same input data files, these components will produce bitwise-identical outputs.

---

## Known Non-Reproducible Aspects (API Drift)

Despite best practices, full bitwise reproducibility cannot be guaranteed for all stages due to external dependencies:

1. **Public Exchange APIs**
   - OHLCV and trade endpoints may change historical availability over time.
   - Rate limits, pagination behavior, or backfill policies may evolve.
2. **Market Evolution**
   - Crypto markets are non-stationary; re-running data collection at a later date yields different samples.
3. **Endpoint Constraints**
   - Trade endpoints often impose implicit or explicit limits (e.g., maximum trades per request or lookback windows).

As a result, strict reproducibility requires **freezing datasets** (e.g., via Zenodo releases) rather than re-querying live APIs.

---

## Verification Procedure

To verify a published run:

1. Obtain the archived run directory (e.g., via Zenodo or GitHub release assets).
2. Recompute checksums:

```bash
shasum -a 256 -c checksums.sha256
```

3. Confirm that all artifacts validate without mismatch.

If checksums match, the run is considered fully reproduced.

---

## Reproduction Workflow (Phase 1)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/collect_data.py --run_id <RUN_ID> [options]
python scripts/eda_generate_figures.py --run_id <RUN_ID>
python scripts/data_summary.py --run_id <RUN_ID>
```

---

## Reproducibility Classification

Following common terminology:
- **Strong reproducibility:** achieved when archived datasets and artifacts are reused.
- **Weak reproducibility:** achieved when live APIs are re-queried under similar conditions.

This project explicitly targets **strong reproducibility** for published results.

---

## Authorship and Responsibility

Reproducibility design and implementation:
- **Carlos Ulisses Flores** — Independent Researcher; CTO & Chief Researcher, Codex Hash Ltda.
