"""Compare mean-reversion backtest returns with gross and buy-and-hold baselines."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ai_trading.mean_reversion_backtest import (
    MeanReversionBacktestResult,
    run_price_mean_reversion_backtest,
)
from ai_trading.strategy_tournament import compare_strategies
from algorithmic_trading.trading_costs import IndiaEquityCostModel


@dataclass(frozen=True)
class MeanReversionComparisonResult:
    """Comparable return streams and their risk-adjusted performance report."""

    return_streams: pd.DataFrame
    comparison: pd.DataFrame


def compare_price_mean_reversion(
    close: pd.Series,
    *,
    lookback: int = 20,
    rsi_period: int = 14,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    oversold_rsi: float = 35.0,
    overbought_rsi: float = 65.0,
    allow_short: bool = False,
    initial_capital: float = 100_000.0,
    cost_bps: float = 10.0,
    cost_model: IndiaEquityCostModel | None = None,
    min_observations: int = 30,
    periods_per_year: float = 252.0,
    risk_free_rate: float = 0.0,
) -> MeanReversionComparisonResult:
    """Compare net strategy, gross strategy and buy-and-hold periodic returns.

    The net stream includes the backtest engine's transaction costs. The gross
    stream uses the same next-bar position but excludes those costs. Buy-and-hold
    uses the market return stream. All three are aligned to identical timestamps
    and ranked by the shared strategy tournament utility.
    """
    backtest: MeanReversionBacktestResult = run_price_mean_reversion_backtest(
        close,
        lookback=lookback,
        rsi_period=rsi_period,
        entry_z=entry_z,
        exit_z=exit_z,
        oversold_rsi=oversold_rsi,
        overbought_rsi=overbought_rsi,
        allow_short=allow_short,
        initial_capital=initial_capital,
        cost_bps=cost_bps,
        cost_model=cost_model,
    )
    equity = backtest.equity_curve
    streams = pd.DataFrame(
        {
            "mean_reversion_net": equity["strategy_return"],
            "mean_reversion_gross": (
                equity["position"] * equity["market_return"]
            ),
            "buy_and_hold": equity["market_return"],
        },
        index=equity.index,
    )
    comparison = compare_strategies(
        {name: streams[name] for name in streams.columns},
        periods_per_year=periods_per_year,
        risk_free_rate=risk_free_rate,
        min_observations=min_observations,
    )
    return MeanReversionComparisonResult(
        return_streams=streams,
        comparison=comparison,
    )
