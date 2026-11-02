"""Tests for the NR4/NR7 research backtest."""

import pandas as pd
import pytest

from ai_trading.narrow_range_breakout_backtest import backtest_narrow_range_breakouts


def test_rejects_invalid_lookback() -> None:
    with pytest.raises(ValueError, match="lookback"):
        backtest_narrow_range_breakouts(pd.DataFrame(), lookback=5)


def test_empty_history_returns_empty_result() -> None:
    result = backtest_narrow_range_breakouts(pd.DataFrame())
    assert result["trades"] == []
    assert result["summary"]["trade_count"] == 0


def test_insufficient_history_does_not_create_trades() -> None:
    index = pd.date_range("2026-10-01 09:15", periods=8, freq="5min")
    frame = pd.DataFrame(
        {
            "Open": [100.0] * 8,
            "High": [101.0] * 8,
            "Low": [99.0] * 8,
            "Close": [100.0] * 8,
        },
        index=index,
    )
    result = backtest_narrow_range_breakouts(frame, lookback=4, atr_window=14)
    assert result["trades"] == []
    assert result["summary"]["trade_count"] == 0


def test_costs_and_capital_parameters_are_validated() -> None:
    with pytest.raises(ValueError, match="capital"):
        backtest_narrow_range_breakouts(pd.DataFrame(), initial_capital=0)
