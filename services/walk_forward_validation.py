"""Chronological walk-forward evaluation helpers for simple quant baselines."""

from __future__ import annotations

import numpy as np
import pandas as pd


def walk_forward_momentum(
    close: pd.Series,
    *,
    train_size: int = 252,
    test_size: int = 63,
    momentum_window: int = 20,
    transaction_cost_bps: float = 10.0,
) -> tuple[pd.DataFrame, pd.Series]:
    """Evaluate a fixed momentum rule on sequential, non-overlapping test windows.

    The training window is used only to establish the first out-of-sample boundary.
    The rule is deliberately not fitted: at each close, positive trailing momentum
    sets exposure for the *next* session. Returns inside each test window are
    strictly out-of-sample relative to that fold's boundary.
    """
    if train_size < momentum_window + 1:
        raise ValueError("train_size must exceed momentum_window by at least one observation")
    if test_size < 1:
        raise ValueError("test_size must be positive")
    if momentum_window < 1:
        raise ValueError("momentum_window must be positive")
    if transaction_cost_bps < 0:
        raise ValueError("transaction_cost_bps cannot be negative")

    prices = pd.to_numeric(close, errors="coerce").dropna()
    prices = prices[~prices.index.duplicated(keep="last")].sort_index()
    prices = prices[prices > 0]
    if len(prices) <= train_size:
        raise ValueError("Not enough prices for an initial training window and test data")

    returns = prices.pct_change()
    momentum = prices.pct_change(momentum_window)
    # Signal at t is only applied to return at t+1.
    exposure = momentum.gt(0).astype(float).shift(1).fillna(0.0)
    turnover = exposure.diff().abs()
    if len(turnover):
        turnover.iloc[0] = abs(exposure.iloc[0])

    strategy_returns = exposure * returns - turnover * (transaction_cost_bps / 10_000.0)
    strategy_returns = strategy_returns.replace([np.inf, -np.inf], np.nan)

    rows: list[dict[str, float | int | str]] = []
    out_of_sample: list[pd.Series] = []
    fold_number = 0
    start = train_size
    while start < len(prices):
        end = min(start + test_size, len(prices))
        test_index = prices.index[start:end]
        fold_returns = strategy_returns.loc[test_index].dropna()
        if fold_returns.empty:
            start = end
            continue
        fold_number += 1
        wealth = (1.0 + fold_returns).cumprod()
        drawdown = wealth / wealth.cummax() - 1.0
        std = float(fold_returns.std(ddof=1))
        sharpe = (
            float(fold_returns.mean() / std * np.sqrt(252))
            if np.isfinite(std) and std > 0
            else float("nan")
        )
        rows.append(
            {
                "fold": fold_number,
                "train_end": str(prices.index[start - 1]),
                "test_start": str(fold_returns.index[0]),
                "test_end": str(fold_returns.index[-1]),
                "test_observations": int(len(fold_returns)),
                "cumulative_return": float(wealth.iloc[-1] - 1.0),
                "annualized_sharpe": sharpe,
                "max_drawdown": float(drawdown.min()),
            }
        )
        out_of_sample.append(fold_returns.rename("strategy_return"))
        start = end

    if not rows:
        raise ValueError("No valid out-of-sample folds could be calculated")
    return pd.DataFrame(rows), pd.concat(out_of_sample).sort_index()
