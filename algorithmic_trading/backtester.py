"""Research backtester for NSE/BSE algorithmic signals.

The existing dashboard backtester remains unchanged. This engine provides a
separate, reusable foundation for testing arbitrary target-position signals
with next-bar execution, transaction costs and portfolio statistics.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from algorithmic_trading.trading_costs import IndiaEquityCostModel


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
    volatility: float
    sharpe_ratio: float | None
    sortino_ratio: float | None
    calmar_ratio: float | None


def _trade_returns(data: pd.DataFrame) -> pd.Series:
    """Return realized return for each directional non-zero position segment."""
    position = data["position"]
    active = position.ne(0)
    starts = active & (~active.shift(1, fill_value=False) | position.ne(position.shift(1)))
    trade_id = starts.cumsum()
    active_returns = data.loc[active, "strategy_return"]

    if active_returns.empty:
        return pd.Series(dtype=float)

    return active_returns.groupby(trade_id.loc[active]).apply(
        lambda values: (1.0 + values).prod() - 1.0
    )


def run_backtest(
    prices: pd.Series,
    signals: pd.Series,
    initial_capital: float = 100_000.0,
    cost_bps: float = 10.0,
    cost_model: IndiaEquityCostModel | None = None,
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
    position_change = data["position"].diff().fillna(data["position"])
    data["turnover"] = position_change.abs()
    data["buy_turnover"] = position_change.clip(lower=0.0)
    data["sell_turnover"] = -position_change.clip(upper=0.0)

    if cost_model is None:
        data["transaction_cost"] = data["turnover"] * (cost_bps / 10_000.0)
    else:
        data["transaction_cost"] = cost_model.cost_fraction(
            data["buy_turnover"], data["sell_turnover"]
        )
    data["strategy_return"] = data["position"] * data["market_return"] - data["transaction_cost"]
    data["strategy_equity"] = initial_capital * (1.0 + data["strategy_return"]).cumprod()
    data["buy_hold_equity"] = initial_capital * (1.0 + data["market_return"]).cumprod()

    peak = data["strategy_equity"].cummax()
    data["drawdown"] = data["strategy_equity"].div(peak).sub(1.0)

    trade_returns = _trade_returns(data)
    wins = trade_returns[trade_returns > 0]
    losses = trade_returns[trade_returns < 0]
    total_return = float(data["strategy_equity"].iloc[-1] / initial_capital - 1.0)

    elapsed_days = (data.index[-1] - data.index[0]).days
    final_equity = float(data["strategy_equity"].iloc[-1])
    if elapsed_days > 0 and final_equity > 0:
        cagr = float((final_equity / initial_capital) ** (365.25 / elapsed_days) - 1.0)
    else:
        cagr = None

    gross_profit = float(wins.sum())
    gross_loss = float(abs(losses.sum()))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else None

    daily_returns = data["strategy_return"].astype(float)
    volatility = float(daily_returns.std(ddof=1) * (252.0**0.5)) if len(daily_returns) > 1 else 0.0
    daily_std = float(daily_returns.std(ddof=1)) if len(daily_returns) > 1 else 0.0
    mean_daily = float(daily_returns.mean()) if len(daily_returns) else 0.0
    downside = daily_returns[daily_returns < 0]
    downside_std = float((downside.pow(2).mean()) ** 0.5) if not downside.empty else 0.0
    sharpe_ratio = float(mean_daily / daily_std * (252.0**0.5)) if daily_std > 0 else None
    sortino_ratio = float(mean_daily / downside_std * (252.0**0.5)) if downside_std > 0 else None
    calmar_ratio = (
        float(cagr / abs(float(data["drawdown"].min())))
        if cagr is not None and float(data["drawdown"].min()) < 0
        else None
    )

    metrics = BacktestMetrics(
        total_return=total_return,
        cagr=cagr,
        max_drawdown=float(data["drawdown"].min()),
        buy_hold_return=float(data["buy_hold_equity"].iloc[-1] / initial_capital - 1.0),
        trade_count=int(len(trade_returns)),
        win_rate=(float(len(wins) / len(trade_returns)) if len(trade_returns) else 0.0),
        profit_factor=profit_factor,
        volatility=volatility,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        calmar_ratio=calmar_ratio,
    )
    return data, metrics
