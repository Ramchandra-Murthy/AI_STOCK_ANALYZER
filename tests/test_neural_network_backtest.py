"""Regression tests for neural-network holdout backtest accounting."""

import numpy as np
import pandas as pd
import pytest

from neural_networks.strategy_backtest import backtest_holdout_signals


def _prices() -> pd.Series:
    dates = pd.date_range("2025-01-01", periods=8, freq="D")
    return pd.Series(
        [100, 101, 102, 103, 104, 105, 106, 107], index=dates, name="Close"
    )


def test_backtest_uses_next_close_entry_and_horizon_close_exit() -> None:
    close = _prices()
    signals = close.index[:2]

    summary, trades = backtest_holdout_signals(
        close, signals, [0.8, 0.9], horizon=2, threshold=0.5, cost_bps_per_side=0
    )

    assert len(trades) == 1
    assert trades.iloc[0]["Signal date"] == close.index[0]
    assert trades.iloc[0]["Entry date"] == close.index[1]
    assert trades.iloc[0]["Exit date"] == close.index[3]
    assert trades.iloc[0]["Gross return"] == pytest.approx(103 / 101 - 1)
    assert trades.iloc[0]["Net return after costs"] == pytest.approx(103 / 101 - 1)
    assert summary.iloc[0]["Trades"] == 1


def test_backtest_charges_entry_and_exit_costs() -> None:
    close = _prices()
    cost_bps = 10
    cost = cost_bps / 10_000
    _, trades = backtest_holdout_signals(
        close,
        close.index[:1],
        [0.8],
        horizon=2,
        threshold=0.5,
        cost_bps_per_side=cost_bps
    )

    expected = (1 - cost) ** 2 * (103 / 101) - 1
    assert trades.iloc[0]["Net return after costs"] == pytest.approx(expected)


def test_backtest_returns_zero_trades_when_threshold_not_met() -> None:
    close = _prices()
    summary, trades = backtest_holdout_signals(
        close,
        close.index[:2],
        [0.8, 0.7],
        horizon=2,
        threshold=0.9,
        cost_bps_per_side=0
    )

    assert trades.empty
    assert summary.iloc[0]["Trades"] == 0
    assert summary.iloc[0]["Total return"] == pytest.approx(0.0)


@pytest.mark.parametrize("probabilities", [[np.nan], [np.inf], [-0.1], [1.1]])
def test_backtest_rejects_invalid_probabilities(probabilities: list[float]) -> None:
    close = _prices()
    with pytest.raises(ValueError, match="probabilities must be finite values"):
        backtest_holdout_signals(close, close.index[:1], probabilities, horizon=2, threshold=0.5)
