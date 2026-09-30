"""Tests for the leakage-safe AI trading ML engine."""

import numpy as np
import pandas as pd

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
