"""Leakage-safe machine-learning model for AI trading intelligence."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ai_trading.features import build_features

FEATURE_COLUMNS = [
    "return_1",
    "return_5",
    "return_20",
    "ema_gap",
    "volatility_20",
    "volume_ratio",
]


@dataclass(frozen=True)
class ModelValidation:
    """Validation metrics and sample counts for a time-ordered model split."""

    accuracy: float
    roc_auc: float | None
    train_samples: int
    test_samples: int
    positive_rate: float


def make_training_dataset(
    frame: pd.DataFrame,
    *,
    horizon: int = 5,
    threshold: float = 0.01,
) -> tuple[pd.DataFrame, pd.Series]:
    """Build explicit two-sided future-return direction labels without leakage."""
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    if threshold < 0:
        raise ValueError("threshold must be non-negative")

    features = build_features(frame)[FEATURE_COLUMNS].copy()
    close = pd.to_numeric(frame["Close"], errors="coerce")
    future_return = close.shift(-horizon) / close - 1.0

    if threshold == 0.0:
        labels = (future_return > 0.0).astype("float")
    else:
        labels = pd.Series(pd.NA, index=frame.index, dtype="Float64")
        labels[future_return >= threshold] = 1.0
        labels[future_return <= -threshold] = 0.0

    labels[future_return.isna()] = pd.NA

    dataset = features.join(labels.rename("target"), how="inner").dropna()
    if dataset.empty:
        return pd.DataFrame(columns=FEATURE_COLUMNS), pd.Series(dtype="int64")

    return dataset[FEATURE_COLUMNS], dataset["target"].astype(int)


def train_model(
    frame: pd.DataFrame,
    *,
    horizon: int = 5,
    threshold: float = 0.01,
    test_fraction: float = 0.2,
) -> tuple[Pipeline, ModelValidation]:
    """Train a logistic model using a chronological, non-random split."""
    if not 0.1 <= test_fraction <= 0.5:
        raise ValueError("test_fraction must be between 0.1 and 0.5")

    x, y = make_training_dataset(frame, horizon=horizon, threshold=threshold)
    if len(x) < 30:
        raise ValueError("at least 30 labelled samples are required")
    if y.nunique() < 2:
        raise ValueError("training data must contain both target classes")

    split = int(len(x) * (1.0 - test_fraction))
    if split < 20 or len(x) - split < 5:
        raise ValueError("training and test windows are too small")

    x_train, x_test = x.iloc[:split], x.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    if y_train.nunique() < 2 or y_test.nunique() < 2:
        raise ValueError("both chronological windows must contain both target classes")

    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )
    model.fit(x_train, y_train)

    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    roc_auc = float(roc_auc_score(y_test, probabilities))
    validation = ModelValidation(
        accuracy=float(accuracy_score(y_test, predictions)),
        roc_auc=roc_auc,
        train_samples=len(x_train),
        test_samples=len(x_test),
        positive_rate=float(y.mean()),
    )
    return model, validation


def predict_latest(model: Pipeline, frame: pd.DataFrame) -> dict[str, float | str]:
    """Return the latest model probability and directional classification."""
    features = build_features(frame)[FEATURE_COLUMNS]
    if features.empty:
        raise ValueError("not enough market history for a prediction")

    probability = float(model.predict_proba(features.iloc[[-1]])[0, 1])
    signal = "LONG" if probability >= 0.5 else "SHORT"
    confidence = abs(probability - 0.5) * 2.0
    return {
        "probability_up": probability,
        "confidence": confidence,
        "signal": signal,
    }
