"""Model calibration and monitoring metrics for AI trading models."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.metrics import accuracy_score, brier_score_loss

from ai_trading.ml_model import make_training_dataset, train_model


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

    model, validation = train_model(
        frame,
        horizon=horizon,
        threshold=threshold,
        test_fraction=test_fraction,
    )
    x, y = make_training_dataset(frame, horizon=horizon, threshold=threshold)
    test_samples = validation.test_samples
    x_test = x.iloc[-test_samples:]
    y_test = y.iloc[-test_samples:]

    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    average_probability = float(probabilities.mean())
    actual_positive_rate = float(y_test.mean())
    calibration_gap = abs(average_probability - actual_positive_rate)
    metrics = CalibrationMetrics(
        accuracy=float(accuracy_score(y_test, predictions)),
        brier_score=float(brier_score_loss(y_test, probabilities)),
        average_probability=average_probability,
        actual_positive_rate=actual_positive_rate,
        calibration_gap=calibration_gap,
        train_samples=validation.train_samples,
        test_samples=test_samples,
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
