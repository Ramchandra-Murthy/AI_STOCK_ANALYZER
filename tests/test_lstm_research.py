"""Tests for the optional PyTorch LSTM research model."""

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("torch")

from ai_trading.lstm_research import predict_lstm, train_lstm_model


def sample_frame(rows: int = 260) -> pd.DataFrame:
    index = pd.date_range("2022-01-03", periods=rows, freq="B")
    steps = np.arange(rows, dtype=float)
    close = 100 + 0.025 * steps + 2 * np.sin(steps / 5) + 0.7 * np.sin(steps / 1.7)
    volume = 100_000 + 5_000 * np.sin(steps / 7) + steps * 10
    return pd.DataFrame(
        {
            "Open": close * 0.999,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": volume,
        },
        index=index,
    )


def test_lstm_training_returns_chronological_holdout_metrics() -> None:
    model, metrics = train_lstm_model(
        sample_frame(),
        sequence_length=10,
        horizon=3,
        test_fraction=0.2,
        epochs=2,
        random_state=11,
    )
    assert metrics.train_samples > metrics.test_samples
    assert 0 <= metrics.accuracy <= 1
    assert metrics.roc_auc is None or 0 <= metrics.roc_auc <= 1
    assert model["sequence_length"] == 10


def test_lstm_prediction_uses_latest_available_features() -> None:
    frame = sample_frame()
    model, _ = train_lstm_model(
        frame,
        sequence_length=10,
        horizon=3,
        epochs=2,
        random_state=11,
    )
    prediction = predict_lstm(model, frame)
    assert 0 <= prediction["probability_up"] <= 1
    assert 0 <= prediction["confidence"] <= 1
    assert prediction["signal"] in {"LONG", "SHORT"}


def test_lstm_rejects_invalid_configuration() -> None:
    with pytest.raises(ValueError, match="sequence_length"):
        train_lstm_model(sample_frame(), sequence_length=1)
