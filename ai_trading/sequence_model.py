"""Leakage-safe sequence learning engine for AI trading research."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

from ai_trading.ml_model import FEATURE_COLUMNS, make_training_dataset


@dataclass(frozen=True)
class SequenceValidation:
    accuracy: float
    roc_auc: float | None
    train_samples: int
    test_samples: int
    positive_rate: float


def make_sequences(
    frame: pd.DataFrame,
    *,
    sequence_length: int = 20,
    horizon: int = 5,
    threshold: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Build chronological fixed-length feature sequences and labels."""
    if sequence_length < 2:
        raise ValueError("sequence_length must be at least 2")

    features, labels = make_training_dataset(
        frame,
        horizon=horizon,
        threshold=threshold,
    )
    if len(features) < sequence_length:
        raise ValueError("not enough samples for sequence training")

    scaler = StandardScaler()
    scaled = scaler.fit_transform(features[FEATURE_COLUMNS])
    x = np.asarray(
        [scaled[i - sequence_length + 1 : i + 1] for i in range(sequence_length - 1, len(scaled))],
        dtype=float,
    )
    y = labels.iloc[sequence_length - 1 :].to_numpy(dtype=int)
    return x, y


def train_sequence_model(
    frame: pd.DataFrame,
    *,
    sequence_length: int = 20,
    horizon: int = 5,
    threshold: float = 0.0,
    test_fraction: float = 0.2,
) -> tuple[dict[str, object], SequenceValidation]:
    """Train a lightweight sequence model with chronological validation."""
    x, y = make_sequences(
        frame,
        sequence_length=sequence_length,
        horizon=horizon,
        threshold=threshold,
    )
    if not 0.1 <= test_fraction < 0.5:
        raise ValueError("test_fraction must be between 0.1 and 0.5")

    split = max(1, int(len(x) * (1.0 - test_fraction)))
    if split >= len(x):
        raise ValueError("test split leaves no validation samples")
    train_x, test_x = x[:split], x[split:]
    train_y, test_y = y[:split], y[split:]
    if np.unique(train_y).size < 2:
        raise ValueError("training data must contain both classes")

    from sklearn.neural_network import MLPClassifier

    model = MLPClassifier(
        hidden_layer_sizes=(32, 16),
        max_iter=500,
        random_state=42,
        early_stopping=True,
    )
    model.fit(train_x.reshape(len(train_x), -1), train_y)
    probabilities = model.predict_proba(test_x.reshape(len(test_x), -1))[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    accuracy = float(accuracy_score(test_y, predictions))
    roc_auc = float(roc_auc_score(test_y, probabilities)) if np.unique(test_y).size > 1 else None
    validation = SequenceValidation(
        accuracy=accuracy,
        roc_auc=roc_auc,
        train_samples=len(train_x),
        test_samples=len(test_x),
        positive_rate=float(y.mean()),
    )
    return {"model": model}, validation


def predict_sequence(
    trained: dict[str, object],
    frame: pd.DataFrame,
    *,
    sequence_length: int = 20,
) -> dict[str, float | str]:
    """Predict the latest sequence."""
    x, _ = make_sequences(frame, sequence_length=sequence_length, horizon=1)
    model = trained["model"]
    probabilities = model.predict_proba(x[-1:].reshape(1, -1))[:, 1]
    probability = float(probabilities[0])
    return {
        "probability_up": probability,
        "confidence": abs(probability - 0.5) * 2.0,
        "signal": "LONG" if probability >= 0.5 else "SHORT",
    }
