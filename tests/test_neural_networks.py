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


def test_baseline_comparison_and_walk_forward_preserve_chronology() -> None:
    from neural_networks.evaluation import (
        compare_holdout_baselines,
        walk_forward_evaluation,
    )

    data = sample_ohlcv(rows=520)
    features, target = build_direction_dataset(data, horizon=5)

    comparison = compare_holdout_baselines(features, target, train_fraction=0.70)
    assert set(comparison["Model"]) == {
        "Majority-class",
        "Logistic regression",
        "MLP",
    }
    assert comparison["Accuracy"].between(0, 1).all()

    walk_forward = walk_forward_evaluation(features, target, n_splits=3)
    assert len(walk_forward) == 9
    assert set(walk_forward["Model"]) == {
        "Majority-class",
        "Logistic regression",
        "MLP",
    }
    assert (walk_forward["Train end"] < walk_forward["Test start"]).all()
    assert walk_forward["Accuracy"].between(0, 1).all()



def test_cost_aware_backtest_uses_non_overlapping_trades_and_costs() -> None:
    from neural_networks.strategy_backtest import backtest_holdout_signals

    data = sample_ohlcv(rows=240)
    signal_dates = data.index[100:180]
    probabilities = np.full(len(signal_dates), 0.9)

    summary_free, trades_free = backtest_holdout_signals(
        data["Close"],
        signal_dates,
        probabilities,
        horizon=5,
        threshold=0.5,
        cost_bps_per_side=0,
    )
    summary_costed, trades_costed = backtest_holdout_signals(
        data["Close"],
        signal_dates,
        probabilities,
        horizon=5,
        threshold=0.5,
        cost_bps_per_side=10,
    )

    assert len(trades_free) > 0
    assert len(trades_free) == len(trades_costed)
    assert (trades_free["Exit date"] < trades_free["Signal date"].shift(-1)).all()
    assert summary_costed.loc[0, "Total return"] <= summary_free.loc[0, "Total return"]
    assert summary_costed.loc[0, "Trades"] == len(trades_costed)


def test_cost_aware_backtest_rejects_empty_signals() -> None:
    from neural_networks.strategy_backtest import backtest_holdout_signals

    data = sample_ohlcv(rows=180)
    with pytest.raises(ValueError, match="at least one holdout signal"):
        backtest_holdout_signals(data["Close"], pd.Index([]), [], horizon=5)
