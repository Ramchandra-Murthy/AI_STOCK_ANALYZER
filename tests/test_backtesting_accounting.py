"""Regression tests for EMA backtest accounting and execution timing."""

import pandas as pd
import pytest

from modules.backtesting import _run_backtest


def _history(close, ema20, ema50):
    return pd.DataFrame(
        {
            "Close": close,
            "EMA20": ema20,
            "EMA50": ema50,
        },
        index=pd.date_range("2025-01-01", periods=len(close), freq="D"),
    )


def test_signal_is_applied_on_following_bar_without_lookahead():
    history = _history(
        close=[100.0, 110.0, 121.0, 108.9],
        ema20=[2.0, 2.0, 3.0, 3.0],
        ema50=[1.0, 1.0, 2.0, 4.0],
    )

    results, metrics = _run_backtest(history, initial_capital=10_000, cost_bps=0)

    assert results["position"].tolist() == [0.0, 1.0, 1.0, 0.0]
    assert metrics["trade_count"] == 1
    assert results["strategy_equity"].iloc[1] == pytest.approx(10_000)


def test_entry_and_exit_costs_reduce_strategy_equity():
    history = _history(
        close=[100.0, 110.0, 121.0, 108.9],
        ema20=[2.0, 2.0, 3.0, 3.0],
        ema50=[1.0, 1.0, 2.0, 4.0],
    )

    free_results, _ = _run_backtest(history, initial_capital=10_000, cost_bps=0)
    cost_results, _ = _run_backtest(history, initial_capital=10_000, cost_bps=10)

    assert cost_results["strategy_equity"].iloc[-1] < free_results["strategy_equity"].iloc[-1]
    assert cost_results["strategy_equity"].iloc[1] == pytest.approx(9_990)


def test_drawdown_is_non_positive_and_metrics_match_equity_series():
    history = _history(
        close=[100.0, 110.0, 99.0, 105.0],
        ema20=[2.0, 2.0, 2.0, 2.0],
        ema50=[1.0, 1.0, 1.0, 1.0],
    )

    results, metrics = _run_backtest(history, initial_capital=10_000, cost_bps=0)

    expected_return = results["strategy_equity"].iloc[-1] / 10_000 - 1
    assert metrics["total_return"] == pytest.approx(expected_return)
    assert metrics["max_drawdown"] == pytest.approx(results["drawdown"].min())
    assert metrics["max_drawdown"] <= 0


def test_invalid_or_insufficient_history_is_rejected():
    with pytest.raises(ValueError, match="unavailable"):
        _run_backtest(None, initial_capital=10_000, cost_bps=10)

    short_history = _history([100.0], [2.0], [1.0])
    with pytest.raises(ValueError, match="Not enough valid price history"):
        _run_backtest(short_history, initial_capital=10_000, cost_bps=10)
