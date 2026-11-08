"""Execution-aware portfolio backtesting using volume-constrained bar fills.

Signals are lagged one bar. The close is used as the bar reference price, so this
is a transparent OHLCV research approximation, not an intrabar or broker simulator.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from algorithmic_trading.backtester import BacktestMetrics
from algorithmic_trading.market_impact import estimate_market_impact_bps
from algorithmic_trading.trading_costs import IndiaEquityCostModel


def run_execution_aware_backtest(
    prices: pd.Series,
    signals: pd.Series,
    volumes: pd.Series,
    volatility: pd.Series,
    initial_capital: float = 100_000.0,
    max_participation: float = 0.10,
    impact_coefficient: float = 0.5,
    half_spread_bps: float = 0.0,
    cost_model: IndiaEquityCostModel | None = None,
) -> tuple[pd.DataFrame, BacktestMetrics]:
    """Backtest target exposures with next-bar, volume-constrained execution.

    Target signals are clipped to [-1, 1] and shifted by one bar. Each bar
    re-targets exposure using prior marked equity; only the volume-limited
    portion fills. Remaining exposure is implicitly retried on later bars.
    Execution impact is embedded in fill prices. Optional statutory/broker
    estimates are deducted separately through cost_model.

    Short exposure is represented with negative shares and cash proceeds;
    financing, borrow fees, margin calls and market impact calibration are
    outside this model.
    """
    if not np.isfinite(initial_capital) or initial_capital <= 0:
        raise ValueError("initial_capital must be finite and greater than zero")
    if not np.isfinite(max_participation) or not 0 < max_participation <= 1:
        raise ValueError("max_participation must be in (0, 1]")
    if not np.isfinite(impact_coefficient) or impact_coefficient < 0:
        raise ValueError("impact_coefficient must be finite and non-negative")
    if not np.isfinite(half_spread_bps) or half_spread_bps < 0:
        raise ValueError("half_spread_bps must be finite and non-negative")

    inputs = (prices, signals, volumes, volatility)
    if any(not series.index.is_unique for series in inputs):
        raise ValueError("inputs must not contain duplicate timestamps")
    ordered_index = prices.index.sort_values()
    if any(not ordered_index.equals(series.index.sort_values()) for series in inputs[1:]):
        raise ValueError("prices, signals, volumes, and volatility must have identical timestamps")
    if len(ordered_index) < 2:
        raise ValueError("at least two aligned observations are required")

    data = pd.DataFrame(
        {
            "price": pd.to_numeric(prices.reindex(ordered_index), errors="coerce"),
            "signal": pd.to_numeric(signals.reindex(ordered_index), errors="coerce"),
            "volume": pd.to_numeric(volumes.reindex(ordered_index), errors="coerce"),
            "volatility": pd.to_numeric(volatility.reindex(ordered_index), errors="coerce"),
        },
        index=ordered_index,
    )
    if not np.isfinite(data.to_numpy(dtype=float)).all():
        raise ValueError("prices, signals, volumes, and volatility must be finite numeric values")
    if (data["price"] <= 0).any():
        raise ValueError("prices must be greater than zero")
    if (data["volume"] < 0).any() or (data["volatility"] < 0).any():
        raise ValueError("volumes and volatility must be non-negative")

    data["position"] = data["signal"].clip(-1.0, 1.0).shift(1).fillna(0.0)
    data["market_return"] = data["price"].pct_change().fillna(0.0)
    cash = float(initial_capital)
    shares = 0.0
    previous_equity = float(initial_capital)
    rows: list[dict[str, float]] = []

    for _, bar in data.iterrows():
        reference_price = float(bar["price"])
        capacity = float(bar["volume"]) * max_participation
        target_shares = float(bar["position"]) * max(previous_equity, 0.0) / reference_price
        desired_delta = target_shares - shares
        filled_quantity = min(abs(desired_delta), capacity)
        signed_fill = float(np.sign(desired_delta) * filled_quantity)
        impact_bps = 0.0
        execution_price = reference_price

        if filled_quantity > 0:
            impact_bps = estimate_market_impact_bps(
                filled_quantity=filled_quantity,
                bar_volume=float(bar["volume"]),
                volatility=float(bar["volatility"]),
                impact_coefficient=impact_coefficient,
                half_spread_bps=half_spread_bps,
            )
            execution_price = reference_price * (
                1.0 + float(np.sign(desired_delta)) * impact_bps / 10_000.0
            )
            cash -= signed_fill * execution_price
            shares += signed_fill

        buy_notional = max(signed_fill, 0.0) * execution_price
        sell_notional = max(-signed_fill, 0.0) * execution_price
        fee_fraction = 0.0
        if cost_model is not None and (buy_notional or sell_notional):
            fee_fraction = float(
                cost_model.cost_fraction(
                    pd.Series([buy_notional / max(previous_equity, 1e-12)]),
                    pd.Series([sell_notional / max(previous_equity, 1e-12)]),
                ).iloc[0]
            )
            cash -= previous_equity * fee_fraction

        equity = cash + shares * reference_price
        remaining_quantity = abs(target_shares - shares)
        rows.append(
            {
                "price": reference_price,
                "volume": float(bar["volume"]),
                "position": float(bar["position"]),
                "target_shares": target_shares,
                "shares": shares,
                "filled_quantity": filled_quantity,
                "remaining_quantity": remaining_quantity,
                "participation_rate": (
                    filled_quantity / float(bar["volume"]) if bar["volume"] > 0 else 0.0
                ),
                "impact_bps": impact_bps,
                "execution_price": execution_price,
                "executed_notional": filled_quantity * execution_price,
                "transaction_cost": previous_equity * fee_fraction,
                "cash": cash,
                "equity": equity,
                "strategy_return": equity / previous_equity - 1.0 if previous_equity > 0 else 0.0,
                "market_return": float(bar["market_return"]),
            }
        )
        previous_equity = equity

    result = pd.DataFrame(rows, index=ordered_index)
    result.index.name = prices.index.name
    result["strategy_equity"] = result["equity"]
    result["buy_hold_equity"] = initial_capital * (1.0 + result["market_return"]).cumprod()
    result["drawdown"] = result["strategy_equity"].div(
        result["strategy_equity"].cummax()
    ).sub(1.0)

    active = result["position"].ne(0)
    starts = active & (
        ~active.shift(1, fill_value=False) | result["position"].ne(result["position"].shift(1))
    )
    trade_ids = starts.cumsum()
    trade_returns = (
        result.loc[active, "strategy_return"]
        .groupby(trade_ids.loc[active])
        .apply(lambda values: (1.0 + values).prod() - 1.0)
    )
    wins = trade_returns[trade_returns > 0]
    losses = trade_returns[trade_returns < 0]
    elapsed_days = (ordered_index[-1] - ordered_index[0]).days
    final_equity = float(result["equity"].iloc[-1])
    cagr = (
        float((final_equity / initial_capital) ** (365.25 / elapsed_days) - 1.0)
        if elapsed_days > 0 and final_equity > 0
        else None
    )
    daily_returns = result["strategy_return"].astype(float)
    daily_std = float(daily_returns.std(ddof=1)) if len(daily_returns) > 1 else 0.0
    mean_daily = float(daily_returns.mean())
    downside = daily_returns[daily_returns < 0]
    downside_std = float(np.sqrt(downside.pow(2).mean())) if not downside.empty else 0.0
    max_drawdown = float(result["drawdown"].min())
    metrics = BacktestMetrics(
        total_return=float(final_equity / initial_capital - 1.0),
        cagr=cagr,
        max_drawdown=max_drawdown,
        buy_hold_return=float(result["buy_hold_equity"].iloc[-1] / initial_capital - 1.0),
        trade_count=int(len(trade_returns)),
        win_rate=float(len(wins) / len(trade_returns)) if len(trade_returns) else 0.0,
        profit_factor=float(wins.sum() / abs(losses.sum())) if not losses.empty else None,
        volatility=float(daily_std * np.sqrt(252.0)),
        sharpe_ratio=float(mean_daily / daily_std * np.sqrt(252.0)) if daily_std > 0 else None,
        sortino_ratio=(
            float(mean_daily / downside_std * np.sqrt(252.0)) if downside_std > 0 else None
        ),
        calmar_ratio=(
            float(cagr / abs(max_drawdown)) if cagr is not None and max_drawdown < 0 else None
        ),
    )
    return result, metrics
