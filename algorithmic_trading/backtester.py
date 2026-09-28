"""Research backtester for NSE/BSE algorithmic signals.

The existing dashboard backtester remains unchanged. This engine provides a
separate, reusable foundation for testing arbitrary target-position signals
with next-bar execution, transaction costs and portfolio statistics.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class BacktestMetrics:
    """Summary statistics for one historical signal simulation."""

    total_return: float
    cagr: float | None
    max_drawdown: float
    buy_hold_return: float
    trade_count: int
    win_rate: float
    profit_factor: float | None


def run_backtest(
    prices: pd.Series,
    signals: pd.Series,
    initial_capital: float = 100_000.0,
    cost_bps: float = 10.0,
) -> tuple[pd.DataFrame, BacktestMetrics]:
    """Backtest target positions using signals from the preceding bar.

    Signals should be -1, 0 or 1. A signal observed on day *t* is applied to
    the return on day *t+1*, avoiding same-bar look-ahead.
    """
    if initial_capital <= 0:
        raise ValueError("initial_capital must be greater than zero")
    if cost_bps < 0:
        raise ValueError("cost_bps must be non-negative")

    data = pd.concat(
        [
            pd.to_numeric(prices, errors="coerce").rename("price"),
            pd.to_numeric(signals, errors="coerce").rename("signal"),
        ],
        axis=1,
    ).dropna()

    data = data[data["price"] > 0].copy()
    if len(data) < 2:
        raise ValueError("at least two valid price observations are required")

    data["signal"] = data["signal"].clip(-1, 1)
    data["position"] = data["signal"].shift(1).fillna(0.0)
    data["market_return"] = data["price"].pct_change().fillna(0.0)
    data["turnover"] = data["position"].diff().abs().fillna(
        data["position"].abs()
    )

    transaction_cost = cost_bps / 10_000.0
    data["strategy_return"] = (
        data["position"] * data["market_return"]
        - data["turnover"] * transaction_cost
    )
    data["strategy_equity"] = initial_capital * (
        1.0 + data["strategy_return"]
    ).cumprod()
    data["buy_hold_equity"] = initial_capital * (
        1.0 + data["market_return"]
    ).cumprod()

    peak = data["strategy_equity"].cummax()
    data["drawdown"] = data["strategy_equity"].div(peak).sub(1.0)

    trade_returns = data.loc[
        data["position"].ne(0) & data["position"].ne(data["position"].shift(1)),
        "strategy_return",
    ]
    wins = trade_returns[trade_returns > 0]
    losses = trade_returns[trade_returns < 0]
    total_return = float(data["strategy_equity"].iloc[-1] / initial_capital - 1.0)

    elapsed_days = (data.index[-1] - data.index[0]).days
    final_equity = float(data["strategy_equity"].iloc[-1])
    if elapsed_days > 0 and final_equity > 0:
        cagr = float(
            (final_equity / initial_capital) ** (365.25 / elapsed_days) - 1.0
        )
    else:
        cagr = None

    gross_profit = float(wins.sum())
    gross_loss = float(abs(losses.sum()))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else None

    metrics = BacktestMetrics(
        total_return=total_return,
        cagr=cagr,
        max_drawdown=float(data["drawdown"].min()),
        buy_hold_return=float(data["buy_hold_equity"].iloc[-1] / initial_capital - 1.0),
        trade_count=int(data["turnover"].gt(0).sum()),
        win_rate=float(len(wins) / len(trade_returns)) if len(trade_returns) else 0.0,
        profit_factor=profit_factor,
    )
    return data, metrics
