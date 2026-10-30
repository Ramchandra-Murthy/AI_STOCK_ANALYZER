from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ai_trading.mean_reversion_comparison import compare_price_mean_reversion
from algorithmic_trading.trading_costs import IndiaEquityCostModel


def _prices(periods: int = 100) -> pd.Series:
    index = pd.date_range("2026-01-01", periods=periods, freq="D")
    trend = np.linspace(100.0, 112.0, periods)
    cycle = np.sin(np.arange(periods) / 3.0) * 3.0
    return pd.Series(trend + cycle, index=index)


def test_comparison_contains_net_gross_and_buy_hold_streams():
    result = compare_price_mean_reversion(
        _prices(),
        lookback=10,
        rsi_period=3,
        entry_z=0.8,
        oversold_rsi=50.0,
        cost_bps=0.0,
        min_observations=20,
    )

    assert list(result.return_streams.columns) == [
        "mean_reversion_net",
        "mean_reversion_gross",
        "buy_and_hold",
    ]
    assert result.return_streams.index.equals(_prices().index)
    assert set(result.comparison["strategy"]) == set(result.return_streams.columns)
    assert result.comparison["observations"].eq(100).all()


def test_transaction_costs_reduce_net_return_stream():
    close = _prices()
    free = compare_price_mean_reversion(
        close,
        lookback=10,
        rsi_period=3,
        entry_z=0.8,
        oversold_rsi=50.0,
        cost_bps=0.0,
    )
    charged = compare_price_mean_reversion(
        close,
        lookback=10,
        rsi_period=3,
        entry_z=0.8,
        oversold_rsi=50.0,
        cost_bps=25.0,
    )

    assert (
        charged.return_streams["mean_reversion_net"]
        <= free.return_streams["mean_reversion_net"] + 1e-12
    ).all()
    pd.testing.assert_series_equal(
        charged.return_streams["mean_reversion_gross"],
        free.return_streams["mean_reversion_gross"],
    )


def test_comparison_supports_india_equity_cost_model():
    result = compare_price_mean_reversion(
        _prices(),
        lookback=10,
        rsi_period=3,
        entry_z=0.8,
        oversold_rsi=50.0,
        cost_model=IndiaEquityCostModel(brokerage_bps=5.0, slippage_bps=2.0),
    )

    assert np.isfinite(result.return_streams.to_numpy()).all()
    assert "mean_reversion_net" in set(result.comparison["strategy"])


def test_comparison_validates_minimum_observations():
    with pytest.raises(ValueError, match="min_observations"):
        compare_price_mean_reversion(_prices(), min_observations=0)
