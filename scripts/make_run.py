"""
make_run.py
===========

Run initialization utility for reproducible scientific experiments.

A "run" is the atomic unit of scientific evidence in this project.

A run MUST:
- be uniquely identifiable,
- record code version and environment,
- declare its parameters,
- produce auditable artifacts.

If a result cannot be traced to a run, it does not exist scientifically.
"""

import argparse
import datetime as dt
import subprocess
from pathlib import Path
from typing import Dict

from hash_utils import environment_fingerprint, save_json


# ---------------------------------------------------------------------
# Git utilities
# ---------------------------------------------------------------------

def get_git_commit_hash() -> str:
    """
    Return the current git commit hash.

    Scientific rationale
    --------------------
    Results are only meaningful if tied to an immutable code state.
    """
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
    except Exception:
        return "UNKNOWN"


# ---------------------------------------------------------------------
# Run ID generation
# ---------------------------------------------------------------------

def generate_run_id() -> str:
    """
    Generate a run identifier based on UTC timestamp.

    Format
    ------
    YYYYMMDDTHHMMSSZ

    Example
    -------
    20260116T113045Z
    """
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main(params: Dict):
    run_id = generate_run_id()

    run_dir = Path("runs") / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    manifest = {
        "run_id": run_id,
        "created_utc": dt.datetime.now(dt.UTC).isoformat() + "Z",
        "git": {
            "commit_hash": get_git_commit_hash(),
        },
        "environment": environment_fingerprint(),
        "parameters": params,
        "artifacts": {
            "data": [],
            "figures": [],
            "metrics": None,
        },
        "notes": (
            "This manifest initializes a scientific run. "
            "Artifacts must be added and checksummed after execution."
        ),
    }

    manifest_path = run_dir / "manifest.json"
    save_json(manifest, manifest_path)

    print(f"[OK] Run initialized: {run_dir}")
    print(f"[OK] Manifest created: {manifest_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Initialize a reproducible scientific run."
    )

    # Placeholder for future parameters (data window, symbol, model config, etc.)
    parser.add_argument(
        "--note",
        type=str,
        default="",
        help="Optional human-readable note for this run.",
    )

    args = parser.parse_args()

    params = {
        "note": args.note
    }

    main(params)
