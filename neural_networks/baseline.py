"""Research-only MLP baseline for daily direction classification."""

from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def chronological_split(
    features: pd.DataFrame,
    target: pd.Series,
    train_fraction: float = 0.70,
    horizon: int = 0,
):
    """Split chronologically and purge training labels that overlap the test period.

    Labels in this pipeline use prices through signal row + horizon + 1
    (entry at the next close, exit after the holding horizon). Purging
    horizon + 1 rows keeps each training outcome window before the test period.
    """
    if not 0.5 <= train_fraction < 0.95:
        raise ValueError("train_fraction must be in [0.5, 0.95)")
    if horizon < 0:
        raise ValueError("horizon must be non-negative")
    if not features.index.equals(target.index):
        raise ValueError("features and target must have identical indexes")
    split_at = int(len(features) * train_fraction)
    train_end = split_at - (horizon + 1)
    if train_end < 100 or len(features) - split_at < 30:
        raise ValueError("Need at least 100 purged training and 30 test observations")
    return (
        features.iloc[:train_end],
        features.iloc[split_at:],
        target.iloc[:train_end],
        target.iloc[split_at:],
    )


def train_baseline(
    features: pd.DataFrame,
    target: pd.Series,
    train_fraction: float = 0.70,
    random_state: int = 42,
    horizon: int = 0,
) -> tuple[Pipeline, dict[str, Any]]:
    """Train an MLP and report holdout metrics using a chronological split."""
    X_train, X_test, y_train, y_test = chronological_split(features, target, train_fraction, horizon)
    if y_train.nunique() < 2:
        raise ValueError("Training target must contain both classes")
    model = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "network",
                MLPClassifier(
                    hidden_layer_sizes=(32, 16),
                    activation="relu",
                    alpha=0.01,
                    max_iter=300,
                    early_stopping=False,
                    random_state=random_state,
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)
    classes = list(model.named_steps["network"].classes_)
    probabilities = model.predict_proba(X_test)[:, classes.index(1)]
    predictions = (probabilities >= 0.5).astype(int)
    metrics: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "test_samples": int(len(y_test)),
        "train_samples": int(len(y_train)),
        "train_end": str(X_train.index[-1].date()),
        "train_positive": int((y_train == 1).sum()),
        "train_negative": int((y_train == 0).sum()),
        "test_positive": int((y_test == 1).sum()),
        "test_negative": int((y_test == 0).sum()),
        "probability_up": probabilities,
        "actual": y_test.to_numpy(),
    }
    if y_test.nunique() == 2:
        metrics["roc_auc"] = float(roc_auc_score(y_test, probabilities))
    return model, metrics
