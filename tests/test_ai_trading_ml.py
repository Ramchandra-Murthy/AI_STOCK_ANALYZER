"""Tests for the leakage-safe AI trading ML engine."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from ai_trading.ml_model import make_training_dataset, predict_latest, train_model


def _market_frame(rows: int = 180) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    returns = rng.normal(0.0005, 0.02, rows)
    close = 100.0 * np.exp(np.cumsum(returns))
    return pd.DataFrame(
        {
            "Close": close,
            "Volume": rng.integers(900_000, 1_100_000, rows),
        }
    )


def test_training_dataset_uses_future_label_without_feature_leakage() -> None:
    frame = _market_frame()
    features, labels = make_training_dataset(frame, horizon=5, threshold=0.0)
    assert len(features) == len(labels)
    assert len(features) < len(frame)
    assert "target" not in features.columns


def test_training_dataset_excludes_invalid_close_prices() -> None:
    frame = pd.DataFrame(
        {
            "Close": [100.0, 101.0, 0.0, 103.0, float("inf"), 105.0, 106.0],
            "Volume": [1_000_000] * 7,
        }
    )
    feature_frame = pd.DataFrame(
        1.0,
        index=frame.index,
        columns=[
            "return_1",
            "return_5",
            "return_20",
            "ema_gap",
            "volatility_20",
            "volume_ratio",
        ],
    )

    with patch("ai_trading.ml_model.build_features", return_value=feature_frame):
        features, labels = make_training_dataset(frame, horizon=1, threshold=0.0)

    assert features.index.tolist() == [0, 5]
    assert labels.index.tolist() == [0, 5]


@pytest.mark.parametrize("threshold", [float("nan"), float("inf"), float("-inf"), -0.01])
def test_training_dataset_rejects_invalid_thresholds(threshold: float) -> None:
    with pytest.raises(ValueError, match="threshold must be finite and non-negative"):
        make_training_dataset(_market_frame(), threshold=threshold)


def test_directional_threshold_excludes_neutral_returns() -> None:
    frame = pd.DataFrame(
        {
            "Close": [100.0, 100.0, 100.0, 100.0, 100.0, 102.0, 100.0, 98.0, 98.0, 98.0],
            "Volume": [1_000_000] * 10,
        }
    )
    feature_frame = pd.DataFrame(
        1.0,
        index=frame.index,
        columns=[
            "return_1",
            "return_5",
            "return_20",
            "ema_gap",
            "volatility_20",
            "volume_ratio",
        ],
    )

    with patch("ai_trading.ml_model.build_features", return_value=feature_frame):
        _, labels = make_training_dataset(frame, horizon=5, threshold=0.01)

    assert labels.tolist() == [1, 0, 0, 0]


def test_model_trains_with_chronological_validation() -> None:
    frame = _market_frame()
    model, validation = train_model(frame, horizon=5, threshold=0.0)
    assert validation.train_samples > validation.test_samples
    assert 0.0 <= validation.accuracy <= 1.0
    assert validation.roc_auc is not None
    prediction = predict_latest(model, frame)
    assert prediction["signal"] in {"LONG", "SHORT"}
    assert 0.0 <= float(prediction["probability_up"]) <= 1.0
    assert 0.0 <= float(prediction["confidence"]) <= 1.0


def test_validation_purges_training_labels_that_overlap_holdout() -> None:
    frame = _market_frame()
    horizon = 5
    features, _ = make_training_dataset(frame, horizon=horizon, threshold=0.01)
    split = int(len(features) * 0.8)
    positions = frame.index.get_indexer(features.index)
    validation_start = positions[split]
    expected_train_samples = int((positions[:split] + horizon < validation_start).sum())

    _, validation = train_model(frame, horizon=horizon, threshold=0.01)

    assert validation.train_samples == expected_train_samples
    assert validation.test_samples == len(features) - split
    assert validation.train_samples < split


def test_refit_full_uses_all_labelled_observations_after_validation() -> None:
    frame = _market_frame()
    features, _ = make_training_dataset(frame, horizon=5, threshold=0.0)
    fit_sizes: list[int] = []
    original_fit = LogisticRegression.fit

    def spy_fit(self, x: object, y: object, sample_weight: object = None):
        fit_sizes.append(len(x))
        return original_fit(self, x, y, sample_weight=sample_weight)

    with patch.object(LogisticRegression, "fit", spy_fit):
        train_model(frame, horizon=5, threshold=0.0, refit_full=True)

    assert fit_sizes[0] < len(features)
    assert fit_sizes[-1] == len(features)
