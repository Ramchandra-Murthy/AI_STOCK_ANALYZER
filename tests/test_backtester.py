import pandas as pd
import pytest

from algorithmic_trading.backtester import run_backtest


def test_backtest_applies_signal_on_next_bar() -> None:
    prices = pd.Series(
        [100.0, 110.0, 121.0],
        index=pd.date_range("2026-01-01", periods=3, freq="D"),
    )
    signals = pd.Series([1.0, 1.0, 0.0], index=prices.index)

    result, metrics = run_backtest(
        prices,
        signals,
        initial_capital=100_000,
        cost_bps=0,
    )

    assert result["position"].tolist() == [0.0, 1.0, 1.0]
    assert metrics.total_return == pytest.approx(0.21)


def test_transaction_cost_reduces_returns() -> None:
    index = pd.date_range("2026-01-01", periods=3, freq="D")
    prices = pd.Series([100.0, 110.0, 110.0], index=index)
    signals = pd.Series([1.0, 1.0, 0.0], index=index)

    _, free = run_backtest(prices, signals, cost_bps=0)
    _, charged = run_backtest(prices, signals, cost_bps=100)

    assert charged.total_return < free.total_return


def test_invalid_inputs_fail() -> None:
    index = pd.date_range("2026-01-01", periods=2, freq="D")
    prices = pd.Series([100.0, 101.0], index=index)
    signals = pd.Series([1.0, 0.0], index=index)

    with pytest.raises(ValueError, match="initial_capital"):
        run_backtest(prices, signals, initial_capital=0)
