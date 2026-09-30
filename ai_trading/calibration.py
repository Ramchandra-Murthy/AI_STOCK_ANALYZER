"""Model calibration and monitoring metrics for AI trading models."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.metrics import accuracy_score, brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from ai_trading.ml_model import FEATURE_COLUMNS, make_training_dataset


@dataclass(frozen=True)
class CalibrationMetrics:
    """Out-of-sample probability calibration measurements."""

    accuracy: float
    brier_score: float
    average_probability: float
    actual_positive_rate: float
    calibration_gap: float
    train_samples: int
    test_samples: int


def evaluate_calibration(
    frame: pd.DataFrame,
    *,
    horizon: int = 5,
    threshold: float = 0.01,
    test_fraction: float = 0.2,
    bins: int = 5,
) -> tuple[CalibrationMetrics, pd.DataFrame]:
    """Evaluate probability quality on a chronological holdout."""

    if not 0.1 <= test_fraction <= 0.5:
        raise ValueError("test_fraction must be between 0.1 and 0.5")
    if bins < 2 or bins > 10:
        raise ValueError("bins must be between 2 and 10")

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
    model.fit(x_train[FEATURE_COLUMNS], y_train)

    probabilities = model.predict_proba(x_test[FEATURE_COLUMNS])[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    calibration_gap = float(
        abs(float(probabilities.mean()) - float(y_test.mean()))
    )
    metrics = CalibrationMetrics(
        accuracy=float(accuracy_score(y_test, predictions)),
        brier_score=float(brier_score_loss(y_test, probabilities)),
        average_probability=float(probabilities.mean()),
        actual_positive_rate=float(y_test.mean()),
        calibration_gap=calibration_gap,
        train_samples=len(x_train),
        test_samples=len(x_test),
    )

    edges = [i / bins for i in range(bins + 1)]
    bucket = pd.cut(
        probabilities,
        bins=edges,
        include_lowest=True,
        labels=False,
    )
    calibration = pd.DataFrame(
        {
            "probability_bin": bucket,
            "predicted_probability": probabilities,
            "actual": y_test.to_numpy(),
        }
    )
    summary = (
        calibration.groupby("probability_bin", observed=True)
        .agg(
            samples=("actual", "size"),
            predicted_probability=("predicted_probability", "mean"),
            actual_rate=("actual", "mean"),
        )
        .reset_index()
    )
    summary["calibration_gap"] = (
        summary["predicted_probability"] - summary["actual_rate"]
    ).abs()
    return metrics, summary
