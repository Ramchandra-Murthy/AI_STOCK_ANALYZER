import pandas as pd
import pytest

from algorithmic_trading.backtester import run_backtest
from algorithmic_trading.trading_costs import IndiaEquityCostModel


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


def test_reversal_starts_a_new_directional_trade() -> None:
    index = pd.date_range("2026-01-01", periods=4, freq="D")
    prices = pd.Series([100.0, 110.0, 99.0, 99.0], index=index)
    signals = pd.Series([1.0, -1.0, 0.0, 0.0], index=index)

    _, metrics = run_backtest(prices, signals, cost_bps=0)

    assert metrics.trade_count == 2
    assert metrics.win_rate == pytest.approx(1.0)


def test_invalid_inputs_fail() -> None:
    index = pd.date_range("2026-01-01", periods=2, freq="D")
    prices = pd.Series([100.0, 101.0], index=index)
    signals = pd.Series([1.0, 0.0], index=index)

    with pytest.raises(ValueError, match="initial_capital"):
        run_backtest(prices, signals, initial_capital=0)


def test_cost_model_charges_buy_and_sell_turnover_separately() -> None:
    index = pd.date_range("2026-01-01", periods=4, freq="D")
    prices = pd.Series([100.0, 100.0, 100.0, 100.0], index=index)
    signals = pd.Series([1.0, 1.0, -1.0, 0.0], index=index)
    model = IndiaEquityCostModel(
        brokerage_bps=1.0,
        exchange_transaction_bps=1.0,
        stt_sell_bps=2.0,
        stamp_duty_buy_bps=1.0,
        slippage_bps=1.0,
        gst_rate=0.18,
    )

    data, metrics = run_backtest(prices, signals, cost_model=model)

    assert data["buy_turnover"].tolist() == pytest.approx([0.0, 1.0, 0.0, 0.0])
    assert data["sell_turnover"].tolist() == pytest.approx([0.0, 0.0, 0.0, 2.0])
    assert data["transaction_cost"].iloc[1] > 0
    assert data["transaction_cost"].iloc[3] > data["transaction_cost"].iloc[1]
    assert metrics.total_return < 0


def test_india_equity_cost_model_rejects_negative_rates() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        IndiaEquityCostModel(brokerage_bps=-1.0)
