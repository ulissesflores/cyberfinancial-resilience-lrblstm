"""Audit-grade hashing and environment fingerprint utilities.

Scientific intent:
- Ensure that every data artifact produced by the pipeline can be verified
  and referenced immutably.
- Support reproducibility by recording environment metadata.

This module is part of the project's reproducibility contract:
runs/<run_id>/checksums.sha256 must exist for a run to be considered valid.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from collections.abc import Iterable
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute SHA256 hash for a file (streamed).

    Parameters
    ----------
    path:
        File path to hash.
    chunk_size:
        Bytes per read; larger improves performance on big parquet files.

    Returns
    -------
    str
        SHA256 hex digest.
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def write_checksums_sha256(file_paths: Iterable[Path], out_path: Path) -> dict[str, str]:
    """Write checksums.sha256 in standard format.

    Parameters
    ----------
    file_paths : Iterable[Path]
        List of file paths to hash.
    out_path : Path
        Output path for the checksum file.

    Returns
    -------
    dict[str, str]
        Dictionary mapping relative paths to SHA256 hashes.

    Format: <sha256>  <relative_path>

    Scientific rule:
    - relative_path MUST be relative to the directory containing checksums.sha256
      (i.e., the run directory), to keep artifacts portable across machines.

    """
    out_path = out_path.resolve()
    base_dir = out_path.parent.resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    mapping: dict[str, str] = {}
    lines: list[str] = []

    for p in file_paths:
        p = Path(p).resolve()
        digest = sha256_file(p)

        try:
            rel = str(p.relative_to(base_dir))
        except ValueError:
            # If artifact is outside the run directory, still record it,
            # but this should be avoided in this project.
            rel = str(p)

        mapping[rel] = digest
        lines.append(f"{digest}  {rel}")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return mapping


def get_pip_freeze() -> list[str]:
    """Return pip freeze output lines for environment traceability."""
    try:
        output = subprocess.check_output(["pip", "freeze"], stderr=subprocess.DEVNULL).decode(
            "utf-8"
        )
        return [line.strip() for line in output.splitlines() if line.strip()]
    except Exception:
        return []


def environment_fingerprint() -> dict:
    """Capture environment metadata for manifest.json.

    Returns
    -------
    dict
        Dictionary containing environment metadata (platform, python version, etc.).

    Notes
    -----
    - GPU/CUDA fingerprint will be added later in training scripts.
    """
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "architecture": platform.machine(),
        "pip_freeze": get_pip_freeze(),
    }


def save_json(obj: dict, path: Path) -> None:
    """Write a JSON file with stable formatting.

    Parameters
    ----------
    obj : dict
        Dictionary to serialize.
    path : Path
        Output file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")
