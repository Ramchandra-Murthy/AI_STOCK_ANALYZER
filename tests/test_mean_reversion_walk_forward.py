import numpy as np
import pandas as pd
import pytest

from ai_trading.mean_reversion_walk_forward import (
    evaluate_price_mean_reversion_walk_forward,
)


def _price_history(periods: int = 100) -> pd.Series:
    index = pd.date_range("2025-01-01", periods=periods, freq="D")
    trend = np.linspace(100.0, 115.0, periods)
    cycle = np.sin(np.arange(periods) / 3.0) * 3.0
    return pd.Series(trend + cycle, index=index)


def test_mean_reversion_walk_forward_returns_ordered_out_of_sample_folds() -> None:
    result = evaluate_price_mean_reversion_walk_forward(
        _price_history(),
        lookback=10,
        rsi_period=3,
        entry_z=0.8,
        oversold_rsi=50.0,
        min_train_size=40,
        n_splits=3,
        cost_bps=0.0,
    )

    folds = result.fold_metrics
    assert folds["fold"].tolist() == [1, 2, 3]
    assert folds["observations"].sum() == 60
    assert folds["test_start"].is_monotonic_increasing
    assert folds["test_end"].is_monotonic_increasing
    assert result.stability["windows"] == 3.0
    assert 0.0 <= result.positive_fold_fraction <= 1.0
    assert {
        "total_return",
        "max_drawdown",
        "buy_hold_return",
        "trade_count",
        "win_rate",
        "profit_factor",
        "sharpe_ratio",
    }.issubset(folds.columns)


def test_mean_reversion_walk_forward_keeps_fixed_parameters_and_costs() -> None:
    close = _price_history()
    free = evaluate_price_mean_reversion_walk_forward(
        close,
        lookback=10,
        rsi_period=3,
        entry_z=0.8,
        oversold_rsi=50.0,
        min_train_size=40,
        n_splits=3,
        cost_bps=0.0,
    )
    charged = evaluate_price_mean_reversion_walk_forward(
        close,
        lookback=10,
        rsi_period=3,
        entry_z=0.8,
        oversold_rsi=50.0,
        min_train_size=40,
        n_splits=3,
        cost_bps=25.0,
    )

    assert (charged.fold_metrics["total_return"] <= free.fold_metrics["total_return"]).all()


def test_mean_reversion_walk_forward_rejects_insufficient_history() -> None:
    with pytest.raises(ValueError, match="not enough observations"):
        evaluate_price_mean_reversion_walk_forward(
            _price_history(30),
            lookback=10,
            rsi_period=3,
            min_train_size=30,
            n_splits=2,
        )


def test_mean_reversion_walk_forward_rejects_invalid_fold_count() -> None:
    with pytest.raises(ValueError, match="n_splits"):
        evaluate_price_mean_reversion_walk_forward(
            _price_history(),
            lookback=10,
            rsi_period=3,
            min_train_size=40,
            n_splits=0,
        )
