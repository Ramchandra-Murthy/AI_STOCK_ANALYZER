"""Chronological development/validation/test evaluation for mean-reversion research."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ai_trading.mean_reversion_strategy import price_mean_reversion_signals
from algorithmic_trading.backtester import run_backtest
from algorithmic_trading.trading_costs import IndiaEquityCostModel


@dataclass(frozen=True)
class MeanReversionHoldoutResult:
    """Segment metrics and the exact chronological boundaries used."""

    segment_metrics: pd.DataFrame
    boundaries: dict[str, str | int]


def evaluate_mean_reversion_holdout(
    close: pd.Series,
    *,
    lookback: int = 20,
    rsi_period: int = 14,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    oversold_rsi: float = 35.0,
    overbought_rsi: float = 65.0,
    allow_short: bool = False,
    train_fraction: float = 0.60,
    validation_fraction: float = 0.20,
    initial_capital: float = 100_000.0,
    cost_bps: float = 10.0,
    cost_model: IndiaEquityCostModel | None = None,
    min_segment_observations: int = 20,
) -> MeanReversionHoldoutResult:
    """Evaluate one fixed configuration on chronological train/validation/test segments.

    Parameters are supplied before evaluation and are held constant across all
    segments. The final test segment is evaluated last and is not used for
    fitting, tuning or selection. Signals are causal and generated from rolling
    past/current observations; each segment is backtested independently from
    a flat position so positions are not carried across segment boundaries.
    """
    if not isinstance(close, pd.Series) or close.empty:
        raise ValueError("close must be a non-empty pandas Series")
    if not close.index.is_unique or not close.index.is_monotonic_increasing:
        raise ValueError("close index must be unique and chronologically increasing")
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be between 0 and 1")
    if not 0.0 < validation_fraction < 1.0:
        raise ValueError("validation_fraction must be between 0 and 1")
    if train_fraction + validation_fraction >= 1.0:
        raise ValueError("train_fraction + validation_fraction must be less than 1")
    if (
        isinstance(min_segment_observations, bool)
        or not isinstance(min_segment_observations, int)
        or min_segment_observations < 2
    ):
        raise ValueError("min_segment_observations must be an integer of at least 2")

    prices = pd.to_numeric(close, errors="coerce")
    if prices.isna().any() or not pd.Series(prices).map(pd.notna).all():
        raise ValueError("close must contain valid numeric prices")
    if not (prices > 0.0).all():
        raise ValueError("close prices must be positive")

    total = len(prices)
    train_end = int(total * train_fraction)
    validation_end = int(total * (train_fraction + validation_fraction))
    sizes = (train_end, validation_end - train_end, total - validation_end)
    if min(sizes) < min_segment_observations:
        raise ValueError("each segment must meet min_segment_observations")

    signals = price_mean_reversion_signals(
        prices,
        lookback=lookback,
        rsi_period=rsi_period,
        entry_z=entry_z,
        exit_z=exit_z,
        oversold_rsi=oversold_rsi,
        overbought_rsi=overbought_rsi,
        allow_short=allow_short,
    )
    boundaries = {
        "train_end": str(prices.index[train_end - 1]),
        "validation_start": str(prices.index[train_end]),
        "validation_end": str(prices.index[validation_end - 1]),
        "test_start": str(prices.index[validation_end]),
        "test_end": str(prices.index[-1]),
        "train_observations": train_end,
        "validation_observations": validation_end - train_end,
        "test_observations": total - validation_end,
    }

    segments = (
        ("train", 0, train_end),
        ("validation", train_end, validation_end),
        ("test", validation_end, total),
    )
    rows: list[dict[str, float | int | str]] = []
    for name, start, stop in segments:
        segment_prices = prices.iloc[start:stop]
        segment_signals = signals["signal"].iloc[start:stop]
        _, metrics = run_backtest(
            segment_prices,
            segment_signals,
            initial_capital=initial_capital,
            cost_bps=cost_bps,
            cost_model=cost_model,
        )
        rows.append(
            {
                "segment": name,
                "start": str(segment_prices.index[0]),
                "end": str(segment_prices.index[-1]),
                "observations": len(segment_prices),
                "total_return": metrics.total_return,
                "buy_hold_return": metrics.buy_hold_return,
                "sharpe_ratio": (
                    metrics.sharpe_ratio if metrics.sharpe_ratio is not None else float("nan")
                ),
                "max_drawdown": metrics.max_drawdown,
                "trade_count": metrics.trade_count,
                "profit_factor": (
                    metrics.profit_factor if metrics.profit_factor is not None else float("nan")
                ),
            }
        )
    return MeanReversionHoldoutResult(
        segment_metrics=pd.DataFrame(rows),
        boundaries=boundaries,
    )
