"""Backtest RSI-confirmed price mean-reversion signals with the shared engine."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from algorithmic_trading.backtester import BacktestMetrics, run_backtest
from algorithmic_trading.trading_costs import IndiaEquityCostModel
from ai_trading.mean_reversion_strategy import price_mean_reversion_signals


@dataclass(frozen=True)
class MeanReversionBacktestResult:
    """Signals, portfolio path and metrics from a price mean-reversion simulation."""

    signals: pd.DataFrame
    equity_curve: pd.DataFrame
    metrics: BacktestMetrics


def run_price_mean_reversion_backtest(
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
) -> MeanReversionBacktestResult:
    """Generate causal mean-reversion signals and evaluate them with shared costs.

    The unshifted `signal` column is passed to the generic backtester, which
    applies next-bar execution exactly once. The already-shifted `position`
    column is retained in the signal report for inspection but is not re-shifted.
    """
    signals = price_mean_reversion_signals(
        close,
        lookback=lookback,
        rsi_period=rsi_period,
        entry_z=entry_z,
        exit_z=exit_z,
        oversold_rsi=oversold_rsi,
        overbought_rsi=overbought_rsi,
        allow_short=allow_short,
    )
    equity_curve, metrics = run_backtest(
        close,
        signals["signal"],
        initial_capital=initial_capital,
        cost_bps=cost_bps,
        cost_model=cost_model,
    )
    return MeanReversionBacktestResult(
        signals=signals,
        equity_curve=equity_curve,
        metrics=metrics,
    )
