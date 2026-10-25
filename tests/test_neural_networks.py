"""Tests for the isolated neural-network research baseline."""

import numpy as np
import pandas as pd
import pytest

from neural_networks.features import build_direction_dataset, build_features


def sample_ohlcv(rows: int = 180) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = pd.Series(100 + np.arange(rows) * 0.2 + np.sin(np.arange(rows)), index=index)
    return pd.DataFrame(
        {
            "Open": close * 0.999,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": 100_000 + np.arange(rows) * 100,
        },
        index=index,
    )


def test_features_have_expected_columns_and_causal_index() -> None:
    features = build_features(sample_ohlcv())
    assert list(features.columns) == [
        "return_1d",
        "return_5d",
        "return_20d",
        "volatility_20d",
        "relative_volume_20d",
        "range_pct",
    ]


def test_dataset_excludes_rows_without_future_label() -> None:
    data = sample_ohlcv()
    features, target = build_direction_dataset(data, horizon=5)
    assert features.index.equals(target.index)
    assert features.index.max() == data.index[-6]
    assert set(target.unique()).issubset({0, 1})


def test_missing_columns_raise_clear_error() -> None:
    with pytest.raises(ValueError, match="Missing required OHLCV columns"):
        build_features(pd.DataFrame({"Close": [1, 2]}))
