from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ai_trading.mean_reversion_regime import evaluate_mean_reversion_by_regime


def _ohlc(periods: int = 180) -> pd.DataFrame:
    index = pd.date_range("2026-01-01", periods=periods, freq="D")
    trend = np.linspace(100.0, 125.0, periods)
    cycle = np.sin(np.arange(periods) / 3.0) * 3.0
    close = trend + cycle
    return pd.DataFrame(
        {
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
        },
        index=index,
    )


def test_regime_evaluation_returns_aligned_comparisons():
    result = evaluate_mean_reversion_by_regime(
        _ohlc(),
        lookback=10,
        rsi_period=3,
        entry_z=0.8,
        oversold_rsi=50.0,
        min_observations=5,
    )

    assert not result.return_streams.empty
    assert result.return_streams.index.equals(result.regime_labels.index)
    assert set(result.regime_labels.unique()).issubset({"BULLISH", "BEARISH", "RANGE / MIXED"})
    assert set(result.regime_comparisons["strategy"]) == set(result.return_streams.columns)
    assert result.regime_comparisons.groupby("regime")["observations"].nunique().eq(1).all()


def test_regime_labels_are_lagged_one_bar():
    frame = _ohlc()
    result = evaluate_mean_reversion_by_regime(
        frame,
        lookback=10,
        rsi_period=3,
        entry_z=0.8,
        oversold_rsi=50.0,
        min_observations=5,
    )

    assert result.regime_labels.index[0] > frame.index[0]


def test_regime_evaluation_rejects_missing_ohlc_columns():
    with pytest.raises(ValueError, match="High, Low and Close"):
        evaluate_mean_reversion_by_regime(_ohlc().drop(columns="High"))


def test_regime_evaluation_rejects_non_chronological_index():
    frame = _ohlc().iloc[::-1]
    with pytest.raises(ValueError, match="chronologically increasing"):
        evaluate_mean_reversion_by_regime(frame)
