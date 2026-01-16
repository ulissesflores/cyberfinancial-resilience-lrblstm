# manifest.json — Schema (Run Contract)

This document defines the **minimum run contract** for `runs/<run_id>/manifest.json`.

A run is considered **publishable** only if:
1) `runs/<run_id>/manifest.json` exists and validates against this schema, and
2) `runs/<run_id>/checksums.sha256` exists and matches the referenced artifacts.

## 1. Overview

The manifest records:
- provenance (repository, commit, timestamps),
- run parameters,
- produced artifacts (data/figures/tables/logs),
- optional environment fingerprint for reproducibility.

The manifest is designed for **audit-grade reproducibility** (scientific evidence tracking).

## 2. Required fields (minimum)

### `run_id` (string)
- Format: `YYYYMMDDTHHMMSSZ` (UTC)
- Example: `20260116T113811Z`

### `generated_utc` (string, ISO 8601)
- Example: `2026-01-16T15:38:35Z` (or with offset)

### `repository` (string)
- Canonical repository URL (e.g., GitHub).

### `artifacts` (object)
Must include keys (arrays of strings):
- `data`: list of filenames under `runs/<run_id>/`
- `figures`: list of filenames under `runs/<run_id>/figures/`
- `tables`: list of filenames under `runs/<run_id>/tables/`
- `logs`: list of filenames under `runs/<run_id>/`

At least one of `data` must exist for Phase 1.

## 3. Checksums contract

### `runs/<run_id>/checksums.sha256` (file)
This is the canonical checksum source. It must contain lines in the format:

`<sha256>  <relative_path>`

Rules:
- `<relative_path>` MUST be relative to the run directory (`runs/<run_id>/`).
- It MUST include `manifest.json` and all referenced artifacts from `artifacts.*`.

The manifest may optionally store a derived mapping, but it is **not required** if the `.sha256` file exists and is correct.

## 4. Recommended fields (SOTA)

### `git` (object)
- `commit`: git SHA (HEAD)
- `repository_url`: repository URL (may duplicate `repository`)
- `dirty`: boolean (optional)

### `environment` (object)
Environment fingerprint for reproducibility:
- python version
- platform
- pip freeze snapshot (or pointer to it)

### `parameters` (object)
Nested config-like structure:
- `data_collection`: exchange/symbol/timeframe/window
- `eda`: figure settings (dpi, bins, etc.)
- `data_summary`: notes about the generated tables

## 5. Non-goals (explicit)
- The manifest does not claim causal inference.
- Phase 1 uses **public market observables** as proxies; OMS/infra telemetry belongs to Phase 2.