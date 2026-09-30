"""LSTM variants for the LR-BLSTM ablation (Models A-D).

The four models share one architecture -- a two-layer LSTM encoder (128 units)
with an MC-Dropout regulariser and a linear lead-time head -- and differ only by
two switches, exactly as the paper's ablation specifies:

==========  ============  ===========================================
Model       Bayesian      Little penalty
==========  ============  ===========================================
A           no            no   (deterministic baseline)
B           yes           no   (Bayesian LSTM, no physics)
C           no            yes  (physics-regularised, no uncertainty)
D           yes           yes  (full LR-BLSTM)
==========  ============  ===========================================

"Bayesian" is realised through **MC-Dropout**: dropout stays active at inference
and ``mc_samples`` stochastic forward passes give a predictive mean and standard
deviation. The **Little penalty** adds ``alpha * mean((L - lambda * W_hat)^2)``
to the loss, anchoring predictions to the physical invariant ``L = lambda * W``
even when the telemetry target ``W`` is adversarially corrupted.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

FEATURES = ("lambda_t", "L", "mu_t", "ret", "vol")


@dataclass(frozen=True)
class ModelSpec:
    """Switches that define one ablation arm.

    Parameters
    ----------
    name:
        Arm label (``"A"``..``"D"``).
    bayesian:
        If ``True``, dropout is active at inference (MC-Dropout).
    little:
        If ``True``, the Little-Law penalty is added to the training loss.
    """

    name: str
    bayesian: bool
    little: bool


ABLATION: tuple[ModelSpec, ...] = (
    ModelSpec("A", bayesian=False, little=False),
    ModelSpec("B", bayesian=True, little=False),
    ModelSpec("C", bayesian=False, little=True),
    ModelSpec("D", bayesian=True, little=True),
)


class LSTMRegressor(nn.Module):
    """Two-layer LSTM with MC-Dropout head predicting the next lead time.

    Parameters
    ----------
    n_features:
        Number of input channels per timestep.
    hidden:
        LSTM hidden units per layer.
    dropout:
        Dropout probability applied before the linear head (and between LSTM
        layers); kept active at inference for Bayesian arms.
    """

    def __init__(self, n_features: int, hidden: int = 128, dropout: float = 0.1) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden,
            num_layers=2,
            batch_first=True,
            dropout=dropout,
        )
        self.drop = nn.Dropout(dropout)
        self.head = nn.Linear(hidden, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Predict the next-step lead time for a batch of windows.

        Parameters
        ----------
        x:
            Tensor of shape ``(batch, seq_len, n_features)``.

        Returns
        -------
        torch.Tensor
            Predicted lead time, shape ``(batch,)``.
        """
        out, _ = self.lstm(x)
        last = out[:, -1, :]
        return self.head(self.drop(last)).squeeze(-1)


@dataclass
class Dataset:
    """Windowed tensors plus the physical quantities for the Little penalty.

    Attributes
    ----------
    X:
        Inputs, shape ``(n, seq_len, n_features)``.
    y:
        Target lead time at the step after each window.
    L_step, lam_step:
        Observed WIP and arrival rate at the target step (original scale), used
        by the Little penalty and by closed-loop evaluation.
    """

    X: torch.Tensor
    y: torch.Tensor
    L_step: torch.Tensor
    lam_step: torch.Tensor


def build_dataset(series: dict[str, np.ndarray], seq_len: int) -> tuple[Dataset, dict]:
    """Assemble standardised training windows from a simulation trajectory.

    Parameters
    ----------
    series:
        Output of :func:`simulate.simulate`. The target is ``obs_W`` (telemetry
        lead time, adversarially corrupted inside the adversarial window) so the
        Little penalty has something physical to correct toward.
    seq_len:
        Window length.

    Returns
    -------
    tuple[Dataset, dict]
        The dataset and the normalisation statistics (mean/std per feature and
        for the target) needed to invert predictions.
    """
    feats = np.stack([series[k] for k in FEATURES], axis=1).astype(np.float64)
    f_mean = feats.mean(axis=0)
    f_std = feats.std(axis=0) + 1e-9
    feats_n = (feats - f_mean) / f_std

    target = series["obs_W"].astype(np.float64)
    t_mean = float(target.mean())
    t_std = float(target.std() + 1e-9)

    xs, ys, ls, lams = [], [], [], []
    for t in range(seq_len, len(target)):
        xs.append(feats_n[t - seq_len : t])
        ys.append((target[t] - t_mean) / t_std)
        ls.append(series["L"][t])
        lams.append(series["lambda_t"][t])

    ds = Dataset(
        X=torch.tensor(np.array(xs), dtype=torch.float32),
        y=torch.tensor(np.array(ys), dtype=torch.float32),
        L_step=torch.tensor(np.array(ls), dtype=torch.float32),
        lam_step=torch.tensor(np.array(lams), dtype=torch.float32),
    )
    stats = {"f_mean": f_mean, "f_std": f_std, "t_mean": t_mean, "t_std": t_std}
    return ds, stats


def little_penalty(
    pred_W_real: torch.Tensor, L_step: torch.Tensor, lam_step: torch.Tensor
) -> torch.Tensor:
    """Soft penalty enforcing Little's Law on the predicted lead time.

    Parameters
    ----------
    pred_W_real:
        Predicted lead time in original (de-standardised) units.
    L_step, lam_step:
        Observed WIP and arrival rate at the same step.

    Returns
    -------
    torch.Tensor
        Scalar ``mean((L - lambda * W_hat)^2)`` normalised by ``mean(L^2)`` so
        the term is dimensionless and comparable across regimes.
    """
    resid = L_step - lam_step * pred_W_real
    scale = torch.mean(L_step**2) + 1e-6
    return torch.mean(resid**2) / scale


def train_model(
    spec: ModelSpec,
    ds: Dataset,
    stats: dict,
    train_end: int,
    seed: int,
    epochs: int = 12,
    alpha: float = 0.5,
    lr: float = 1e-3,
) -> LSTMRegressor:
    """Train one ablation arm on the calm (in-distribution) prefix.

    Parameters
    ----------
    spec:
        Which arm (controls the Little-penalty switch).
    ds:
        Full windowed dataset.
    stats:
        Normalisation statistics from :func:`build_dataset`.
    train_end:
        Index (in window space) splitting calm training data from the
        out-of-distribution shocked tail.
    seed:
        Per-arm seed for deterministic initialisation and dropout.
    epochs:
        Training epochs.
    alpha:
        Weight of the Little penalty (ignored when ``spec.little`` is ``False``).
    lr:
        Adam learning rate (with cosine annealing).

    Returns
    -------
    LSTMRegressor
        The trained model (left in train mode by the caller as needed).
    """
    torch.manual_seed(seed)
    model = LSTMRegressor(n_features=len(FEATURES))
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    loss_fn = nn.MSELoss()

    Xtr, ytr = ds.X[:train_end], ds.y[:train_end]
    Ltr, lamtr = ds.L_step[:train_end], ds.lam_step[:train_end]
    t_mean, t_std = stats["t_mean"], stats["t_std"]

    model.train()
    batch = 256
    for _ in range(epochs):
        perm = torch.randperm(len(Xtr))
        for i in range(0, len(Xtr), batch):
            idx = perm[i : i + batch]
            opt.zero_grad()
            pred = model(Xtr[idx])
            loss = loss_fn(pred, ytr[idx])
            if spec.little:
                pred_real = pred * t_std + t_mean
                loss = loss + alpha * little_penalty(pred_real, Ltr[idx], lamtr[idx])
            loss.backward()
            opt.step()
        sched.step()
    return model


def predict(
    model: LSTMRegressor, X: torch.Tensor, spec: ModelSpec, stats: dict, mc_samples: int = 30
) -> tuple[np.ndarray, np.ndarray]:
    """Predict lead times with predictive uncertainty (original units).

    Parameters
    ----------
    model:
        Trained model.
    X:
        Input windows.
    spec:
        Arm switches; Bayesian arms use MC-Dropout, deterministic arms use a
        single ``eval`` pass with homoscedastic uncertainty.
    stats:
        Normalisation statistics (to invert standardisation).
    mc_samples:
        Stochastic forward passes for Bayesian arms.

    Returns
    -------
    tuple[numpy.ndarray, numpy.ndarray]
        Predictive mean and standard deviation in original lead-time units.
    """
    t_mean, t_std = stats["t_mean"], stats["t_std"]
    with torch.no_grad():
        if spec.bayesian:
            model.train()  # keep dropout active for MC sampling
            samples = torch.stack([model(X) for _ in range(mc_samples)], dim=0)
            mean = samples.mean(dim=0) * t_std + t_mean
            std = samples.std(dim=0) * t_std
            return mean.numpy(), np.maximum(std.numpy(), 1e-6)
        model.eval()
        mean = model(X) * t_std + t_mean
        # Deterministic arms carry static (homoscedastic) uncertainty.
        std = np.full(len(mean), 0.5 * t_std, dtype=np.float64)
        return mean.numpy(), std
