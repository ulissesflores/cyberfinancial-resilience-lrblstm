"""End-to-end run contract: manifest + checksums + results are produced."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from hash_utils import sha256_file
from train_lr_blstm import main


def test_end_to_end_quick_run(tmp_path, monkeypatch) -> None:
    """A small run produces a valid run directory with matching checksums."""
    monkeypatch.chdir(tmp_path)
    args = argparse.Namespace(seq_len=16, epochs=1, seed=42, n_steps=900)
    run_id = main(args)

    run_dir = Path("runs") / run_id
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "results.json").exists()
    checksums = run_dir / "checksums.sha256"
    assert checksums.exists()

    # Every checksum line must match the artifact on disk.
    for line in checksums.read_text().strip().splitlines():
        digest, rel = line.split("  ", 1)
        assert sha256_file(run_dir / rel) == digest, rel

    # All four arms are present with a resilience index.
    import json

    results = json.loads((run_dir / "results.json").read_text())
    assert set(results["models"]) == {"A", "B", "C", "D"}
    for arm in results["models"].values():
        assert "resilience_index" in arm
    assert os.path.exists(run_dir / "figures" / "fig1_resilience_index.pdf")
