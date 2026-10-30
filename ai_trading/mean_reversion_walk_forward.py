"""Walk-forward evaluation for RSI-confirmed price mean-reversion signals."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ai_trading.mean_reversion_strategy import price_mean_reversion_signals
from ai_trading.walk_forward_stability import stability_summary
from algorithmic_trading.trading_costs import IndiaEquityCostModel
from algorithmic_trading.walk_forward_validation import walk_forward_evaluate


@dataclass(frozen=True)
class MeanReversionWalkForwardResult:
    """Out-of-sample fold metrics and aggregate stability diagnostics."""

    signals: pd.DataFrame
    fold_metrics: pd.DataFrame
    stability: dict[str, float | None]
    positive_fold_fraction: float


def evaluate_price_mean_reversion_walk_forward(
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
    min_train_size: int = 252,
    n_splits: int = 5,
) -> MeanReversionWalkForwardResult:
    """Evaluate causal signals on chronological, non-overlapping test folds.

    Strategy parameters are supplied by the caller and remain fixed across
    folds. The existing walk-forward evaluator does not fit or tune parameters.
    The indicator series is generated once from past-and-current observations;
    only each fold's held-out segment contributes to its reported metrics.
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
    fold_metrics = walk_forward_evaluate(
        close,
        signals["signal"],
        initial_capital=initial_capital,
        cost_bps=cost_bps,
        cost_model=cost_model,
        min_train_size=min_train_size,
        n_splits=n_splits,
    )
    stability = stability_summary(fold_metrics)
    positive_fold_fraction = float((fold_metrics["total_return"] > 0.0).mean())

    return MeanReversionWalkForwardResult(
        signals=signals,
        fold_metrics=fold_metrics,
        stability=stability,
        positive_fold_fraction=positive_fold_fraction,
    )
