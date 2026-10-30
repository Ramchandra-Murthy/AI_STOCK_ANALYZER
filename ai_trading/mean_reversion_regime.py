"""Evaluate mean-reversion return streams conditionally by prior-bar market regime."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ai_trading.mean_reversion_comparison import compare_price_mean_reversion
from ai_trading.strategy_tournament import compare_strategies
from engine.regime_engine import chapter4_regime


@dataclass(frozen=True)
class MeanReversionRegimeResult:
    """Lagged regime labels, aligned returns and per-regime comparisons."""

    regime_labels: pd.Series
    return_streams: pd.DataFrame
    regime_comparisons: pd.DataFrame


def evaluate_mean_reversion_by_regime(
    ohlc: pd.DataFrame,
    *,
    regime_threshold: int = 3,
    min_observations: int = 20,
    periods_per_year: float = 252.0,
    risk_free_rate: float = 0.0,
    lookback: int = 20,
    rsi_period: int = 14,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    oversold_rsi: float = 35.0,
    overbought_rsi: float = 65.0,
    allow_short: bool = False,
    initial_capital: float = 100_000.0,
    cost_bps: float = 10.0,
) -> MeanReversionRegimeResult:
    """Compare strategy streams within regimes known before each return bar.

    Chapter 4 regime labels are shifted by one bar before being joined to
    strategy returns. This prevents the current bar's high/low/close from
    classifying the same bar's return. The shared tournament calculates
    identical metrics and eligibility rules within each regime.
    """
    required = {"High", "Low", "Close"}
    if not isinstance(ohlc, pd.DataFrame) or not required.issubset(ohlc.columns):
        raise ValueError("ohlc must be a DataFrame containing High, Low and Close")
    if ohlc.empty:
        raise ValueError("ohlc must contain at least one row")
    if isinstance(min_observations, bool) or min_observations < 1:
        raise ValueError("min_observations must be a positive integer")

    frame = ohlc.loc[:, ["High", "Low", "Close"]].apply(pd.to_numeric, errors="coerce")
    if not frame.index.is_unique or not frame.index.is_monotonic_increasing:
        raise ValueError("ohlc index must be unique and chronologically increasing")

    comparison = compare_price_mean_reversion(
        frame["Close"],
        lookback=lookback,
        rsi_period=rsi_period,
        entry_z=entry_z,
        exit_z=exit_z,
        oversold_rsi=oversold_rsi,
        overbought_rsi=overbought_rsi,
        allow_short=allow_short,
        initial_capital=initial_capital,
        cost_bps=cost_bps,
        min_observations=min_observations,
        periods_per_year=periods_per_year,
        risk_free_rate=risk_free_rate,
    )
    regimes = chapter4_regime(frame, regime_threshold=regime_threshold)["regime"]
    prior_regimes = regimes.shift(1).reindex(comparison.return_streams.index)
    valid = prior_regimes.notna() & comparison.return_streams.notna().all(axis=1)
    labels = prior_regimes.loc[valid].rename("prior_regime")
    streams = comparison.return_streams.loc[valid].copy()

    rows: list[pd.DataFrame] = []
    for regime in ("BULLISH", "BEARISH", "RANGE / MIXED"):
        mask = labels.eq(regime)
        if not mask.any():
            continue
        metrics = compare_strategies(
            {name: streams.loc[mask, name] for name in streams.columns},
            periods_per_year=periods_per_year,
            risk_free_rate=risk_free_rate,
            min_observations=min_observations,
        )
        metrics.insert(0, "regime", regime)
        rows.append(metrics)

    regime_comparisons = (
        pd.concat(rows, ignore_index=True)
        if rows
        else pd.DataFrame(
            columns=[
                "regime",
                "strategy",
                "observations",
                "total_return",
                "annualized_volatility",
                "sharpe_ratio",
                "max_drawdown",
                "cvar_95",
                "win_rate",
                "profit_factor",
                "eligible",
                "rank",
            ]
        )
    )
    return MeanReversionRegimeResult(
        regime_labels=labels,
        return_streams=streams,
        regime_comparisons=regime_comparisons,
    )
