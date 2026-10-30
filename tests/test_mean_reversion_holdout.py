import numpy as np
import pandas as pd
import pytest

from ai_trading.mean_reversion_holdout import evaluate_mean_reversion_holdout


def _prices(periods: int = 180) -> pd.Series:
    index = pd.date_range("2026-01-01", periods=periods, freq="D")
    trend = np.linspace(100.0, 112.0, periods)
    cycle = np.sin(np.arange(periods) / 3.0) * 3.0
    return pd.Series(trend + cycle, index=index)


def test_holdout_evaluation_returns_chronological_train_validation_test_metrics():
    result = evaluate_mean_reversion_holdout(
        _prices(),
        lookback=10,
        rsi_period=3,
        entry_z=0.8,
        oversold_rsi=50.0,
        train_fraction=0.6,
        validation_fraction=0.2,
        min_segment_observations=20,
    )

    assert result.segment_metrics["segment"].tolist() == ["train", "validation", "test"]
    assert result.segment_metrics["observations"].tolist() == [108, 36, 36]
    assert result.boundaries["train_end"] < result.boundaries["validation_start"]
    assert result.boundaries["validation_end"] < result.boundaries["test_start"]
    assert result.boundaries["test_end"] == str(_prices().index[-1])


def test_holdout_configuration_is_fixed_across_all_segments():
    close = _prices()
    result = evaluate_mean_reversion_holdout(
        close,
        lookback=10,
        rsi_period=3,
        entry_z=0.8,
        oversold_rsi=50.0,
        cost_bps=0.0,
        min_segment_observations=20,
    )
    charged = evaluate_mean_reversion_holdout(
        close,
        lookback=10,
        rsi_period=3,
        entry_z=0.8,
        oversold_rsi=50.0,
        cost_bps=25.0,
        min_segment_observations=20,
    )

    assert (
        charged.segment_metrics["total_return"] <= (result.segment_metrics["total_return"] + 1e-12)
    ).all()


def test_holdout_rejects_invalid_split_fractions():
    with pytest.raises(ValueError, match="less than 1"):
        evaluate_mean_reversion_holdout(_prices(), train_fraction=0.7, validation_fraction=0.3)


def test_holdout_rejects_nonchronological_index():
    close = _prices().iloc[::-1]
    with pytest.raises(ValueError, match="chronologically increasing"):
        evaluate_mean_reversion_holdout(close)


def test_holdout_rejects_insufficient_segment_history():
    with pytest.raises(ValueError, match="each segment"):
        evaluate_mean_reversion_holdout(_prices(30), min_segment_observations=20)
