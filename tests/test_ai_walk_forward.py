"""Tests for the leakage-safe AI walk-forward backtester."""

import numpy as np
import pandas as pd

from ai_trading.walk_forward import walk_forward_backtest


def _market_frame(rows: int = 240) -> pd.DataFrame:
    rng = np.random.default_rng(123)
    returns = rng.normal(0.0008, 0.015, rows)
    close = 100.0 * np.exp(np.cumsum(returns))
    return pd.DataFrame(
        {
            "Close": close,
            "Volume": rng.integers(900_000, 1_100_000, rows),
        }
    )


def test_walk_forward_backtest_has_non_overlapping_trades() -> None:
    trades, result = walk_forward_backtest(
        _market_frame(),
        horizon=5,
        threshold=0.0,
        initial_train=100,
    )
    assert not trades.empty
    assert result.trades >= 0
    assert result.final_equity > 0.0
    assert result.max_drawdown <= 0.0
    assert 0.0 <= result.win_rate <= 1.0

    entries = pd.to_datetime(trades["entry_index"])
    exits = pd.to_datetime(trades["exit_index"])
    if len(entries) > 1:
        assert all(
            entries.iloc[i] >= exits.iloc[i - 1] for i in range(1, len(entries))
        )


def test_backtest_respects_transaction_costs() -> None:
    frame = _market_frame()
    _, free_result = walk_forward_backtest(
        frame,
        horizon=5,
        threshold=0.0,
        initial_train=100,
        transaction_cost_bps=0.0,
    )
    _, costly_result = walk_forward_backtest(
        frame,
        horizon=5,
        threshold=0.0,
        initial_train=100,
        transaction_cost_bps=20.0,
    )
    assert costly_result.final_equity <= free_result.final_equity
