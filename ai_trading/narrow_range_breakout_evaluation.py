"""Evaluation summaries for NR4/NR7 research backtests (no order execution)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd


def evaluate_narrow_range_backtest(
    result: Mapping[str, Any],
    *,
    initial_capital: float = 10_000.0,
) -> dict[str, Any]:
    """Build an evaluation report from backtest trade records.

    Metrics are calculated from net P&L. Breakdowns are descriptive and do not
    imply statistical significance or future profitability.
    """
    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive")

    raw_trades = result.get("trades", [])
    if not isinstance(raw_trades, Sequence) or isinstance(raw_trades, (str, bytes)):
        raise ValueError("trades must be a sequence")

    trades = [dict(trade) for trade in raw_trades]
    if not trades:
        return {
            "summary": {
                "trade_count": 0,
                "win_rate_pct": 0.0,
                "net_pnl": 0.0,
                "expectancy": 0.0,
                "profit_factor": None,
                "average_r": 0.0,
                "max_drawdown_pct": 0.0,
                "best_trade": None,
                "worst_trade": None,
                "consecutive_wins": 0,
                "consecutive_losses": 0,
            },
            "breakdowns": {},
        }

    frame = pd.DataFrame(trades)
    required = {"net_pnl", "r_multiple", "pattern", "side", "exit_reason"}
    if not required.issubset(frame.columns):
        missing = sorted(required - set(frame.columns))
        raise ValueError(f"trades missing required fields: {missing}")

    frame["net_pnl"] = pd.to_numeric(frame["net_pnl"], errors="raise")
    frame["r_multiple"] = pd.to_numeric(frame["r_multiple"], errors="raise")
    pnls = frame["net_pnl"].astype(float)
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]
    equity = initial_capital + pnls.cumsum()
    peak = equity.cummax().clip(lower=initial_capital)
    drawdown_pct = (equity / peak - 1.0) * 100.0

    win_streak = loss_streak = max_win_streak = max_loss_streak = 0
    for pnl in pnls:
        if pnl > 0:
            win_streak += 1
            loss_streak = 0
        elif pnl < 0:
            loss_streak += 1
            win_streak = 0
        else:
            win_streak = loss_streak = 0
        max_win_streak = max(max_win_streak, win_streak)
        max_loss_streak = max(max_loss_streak, loss_streak)

    summary = {
        "trade_count": len(frame),
        "win_rate_pct": 100.0 * len(wins) / len(frame),
        "net_pnl": float(pnls.sum()),
        "expectancy": float(pnls.mean()),
        "profit_factor": float(wins.sum() / abs(losses.sum())) if len(losses) else None,
        "average_r": float(frame["r_multiple"].mean()),
        "max_drawdown_pct": float(drawdown_pct.min()),
        "best_trade": float(pnls.max()),
        "worst_trade": float(pnls.min()),
        "consecutive_wins": max_win_streak,
        "consecutive_losses": max_loss_streak,
    }

    breakdowns: dict[str, dict[str, dict[str, float | int | None]]] = {}
    for dimension in ("pattern", "side", "exit_reason"):
        groups: dict[str, dict[str, float | int | None]] = {}
        for key, group in frame.groupby(dimension, dropna=False):
            group_pnl = group["net_pnl"].astype(float)
            group_wins = group_pnl[group_pnl > 0]
            group_losses = group_pnl[group_pnl < 0]
            groups[str(key)] = {
                "trade_count": int(len(group)),
                "win_rate_pct": float(100.0 * len(group_wins) / len(group)),
                "net_pnl": float(group_pnl.sum()),
                "expectancy": float(group_pnl.mean()),
                "profit_factor": (
                    float(group_wins.sum() / abs(group_losses.sum())) if len(group_losses) else None
                ),
            }
        breakdowns[dimension] = groups

    return {"summary": summary, "breakdowns": breakdowns}
