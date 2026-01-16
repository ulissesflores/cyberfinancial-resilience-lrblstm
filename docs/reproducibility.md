# Reproducibility Protocol

## Principle
This project follows an audit-grade reproducibility standard:
code + parameters + data + environment + hashes.

## Execution Levels
- Phase 1: Public market data (proxy-based)
- Phase 2: System telemetry (direct queue observability)

## Required Artifacts per Run
- manifest.json
- checksums.sha256
- data files
- figures
- metrics (if training)

## Valid Run
A run is valid if and only if an external researcher can reproduce
the results using the commit hash and the run manifest.
