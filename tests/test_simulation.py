"""Behaviour and determinism of the cyber-financial simulator."""

from __future__ import annotations

import numpy as np
import torch
from models import build_dataset, little_penalty
from simulate import SimConfig, simulate


def test_determinism_same_seed() -> None:
    """Identical seeds reproduce bit-identical trajectories."""
    a = simulate(SimConfig(n_steps=1200), np.random.default_rng(7))
    b = simulate(SimConfig(n_steps=1200), np.random.default_rng(7))
    for key in a:
        assert np.array_equal(a[key], b[key]), key


def test_different_seed_differs() -> None:
    """Different seeds produce different price paths."""
    a = simulate(SimConfig(n_steps=1200), np.random.default_rng(1))
    b = simulate(SimConfig(n_steps=1200), np.random.default_rng(2))
    assert not np.array_equal(a["price"], b["price"])


def test_volumetric_burst_raises_lambda() -> None:
    """The arrival rate inside the burst window exceeds the calm mean."""
    n = 3000
    series = simulate(SimConfig(n_steps=n), np.random.default_rng(3))
    calm_mean = np.mean(series["lambda_t"][: (2 * n) // 3])
    q = n // 12
    base = (2 * n) // 3
    burst_mean = np.mean(series["lambda_t"][base : base + q])
    assert burst_mean > 3.0 * calm_mean


def test_little_penalty_zero_at_truth() -> None:
    """The Little penalty vanishes when W equals the true L / lambda."""
    series = simulate(SimConfig(n_steps=1000), np.random.default_rng(4))
    _, _ = build_dataset(series, seq_len=16)
    L = torch.tensor(series["L"][16:], dtype=torch.float32)
    lam = torch.tensor(series["lambda_t"][16:], dtype=torch.float32)
    true_W = L / torch.clamp(lam, min=1e-6)
    assert float(little_penalty(true_W, L, lam)) < 1e-6


def test_build_dataset_shapes() -> None:
    """Windowing yields aligned tensors of the expected rank."""
    series = simulate(SimConfig(n_steps=800), np.random.default_rng(5))
    ds, stats = build_dataset(series, seq_len=24)
    assert ds.X.ndim == 3 and ds.X.shape[1] == 24
    assert len(ds.y) == len(ds.L_step) == ds.X.shape[0]
    assert {"f_mean", "f_std", "t_mean", "t_std"} <= set(stats)
