import numpy as np
import pandas as pd
import pytest

from ai_trading.mean_reversion_backtest import run_price_mean_reversion_backtest
from algorithmic_trading.trading_costs import IndiaEquityCostModel


def _reversal_prices() -> pd.Series:
    values = [100.0] * 35 + [96.0, 93.0, 91.0, 92.0, 94.0, 95.0, 97.0, 99.0]
    index = pd.date_range("2026-01-01", periods=len(values), freq="D")
    return pd.Series(values, index=index)


def test_mean_reversion_backtest_uses_shared_next_bar_execution() -> None:
    close = _reversal_prices()
    result = run_price_mean_reversion_backtest(
        close,
        lookback=20,
        rsi_period=3,
        entry_z=1.0,
        oversold_rsi=50.0,
        cost_bps=0.0,
    )

    expected_position = result.signals["signal"].shift(1).fillna(0.0)
    pd.testing.assert_series_equal(
        result.equity_curve["position"],
        expected_position,
        check_names=False,
    )
    assert result.metrics.trade_count >= 1
    assert np.isfinite(result.equity_curve["strategy_equity"]).all()


def test_mean_reversion_backtest_applies_configured_transaction_costs() -> None:
    close = _reversal_prices()
    no_cost = run_price_mean_reversion_backtest(
        close, lookback=20, rsi_period=3, entry_z=1.0, oversold_rsi=50.0, cost_bps=0.0
    )
    with_cost = run_price_mean_reversion_backtest(
        close, lookback=20, rsi_period=3, entry_z=1.0, oversold_rsi=50.0, cost_bps=25.0
    )

    assert with_cost.metrics.total_return <= no_cost.metrics.total_return
    assert with_cost.equity_curve["transaction_cost"].sum() > 0.0


def test_mean_reversion_backtest_accepts_india_equity_cost_model() -> None:
    result = run_price_mean_reversion_backtest(
        _reversal_prices(),
        lookback=20,
        rsi_period=3,
        entry_z=1.0,
        oversold_rsi=50.0,
        cost_model=IndiaEquityCostModel(brokerage_bps=5.0, slippage_bps=2.0),
    )

    assert result.equity_curve["transaction_cost"].sum() >= 0.0
    assert result.metrics.buy_hold_return == pytest.approx(
        result.equity_curve["buy_hold_equity"].iloc[-1] / 100_000.0 - 1.0
    )


def test_mean_reversion_backtest_rejects_misaligned_close_index() -> None:
    close = _reversal_prices()
    with pytest.raises(ValueError, match="identical timestamps"):
        run_price_mean_reversion_backtest(close, signals_close=close)  # type: ignore[call-arg]
