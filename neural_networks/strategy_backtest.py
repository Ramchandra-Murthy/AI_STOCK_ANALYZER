"Cost-aware, long-only backtest for chronological holdout probabilities."

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def backtest_holdout_signals(
    close: pd.Series,
    signal_dates: pd.Index,
    probability_up: Any,
    *,
    horizon: int = 5,
    threshold: float = 0.5,
    cost_bps_per_side: float = 10.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Backtest non-overlapping long-only trades from holdout probabilities.

    Signals are assumed known after the signal-date close. Entries occur at the
    next close and exits occur horizon close-to-close intervals later. Costs are
    charged on entry and exit. This simplified simulation does not model taxes,
    spread, market impact, or execution quality.
    """
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")
    if cost_bps_per_side < 0:
        raise ValueError("cost_bps_per_side cannot be negative")
    if len(signal_dates) != len(probability_up):
        raise ValueError("signal_dates and probability_up must have identical lengths")
    if len(signal_dates) == 0:
        raise ValueError("at least one holdout signal date is required")
    if not pd.Index(signal_dates).is_monotonic_increasing:
        raise ValueError("signal dates must be sorted chronologically")
    if not close.index.is_unique:
        raise ValueError("close index must be unique")
    prices = pd.to_numeric(close, errors="coerce").astype(float)
    prices = prices.replace([np.inf, -np.inf], np.nan)
    if prices.isna().any() or (prices <= 0).any():
        raise ValueError("close prices must be finite and positive")
    if not prices.index.is_monotonic_increasing:
        raise ValueError("close prices must be sorted chronologically")
    if len(prices) < horizon + 3:
        raise ValueError("not enough close prices for the requested horizon")
    if not pd.Index(signal_dates).isin(prices.index).all():
        raise ValueError("every signal date must exist in the close-price index")

    probabilities = np.asarray(probability_up, dtype=float)
    if not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("probabilities must be finite values between 0 and 1")

    cost = float(cost_bps_per_side) / 10_000.0
    strategy_daily = pd.Series(0.0, index=prices.index, name="Strategy daily return")
    trades: list[dict[str, Any]] = []
    next_signal_position = -1

    for signal_date, probability in zip(signal_dates, probabilities, strict=True):
        signal_position = prices.index.get_loc(signal_date)
        if signal_position < next_signal_position or probability < threshold:
            continue
        entry_position = signal_position + 1
        exit_position = entry_position + horizon
        if exit_position >= len(prices):
            continue

        entry_date = prices.index[entry_position]
        exit_date = prices.index[exit_position]
        entry_price = float(prices.iloc[entry_position])
        exit_price = float(prices.iloc[exit_position])
        gross_return = exit_price / entry_price - 1.0
        net_return = (1.0 - cost) ** 2 * (1.0 + gross_return) - 1.0

        strategy_daily.loc[entry_date] -= cost
        for position in range(entry_position + 1, exit_position + 1):
            daily_return = prices.iloc[position] / prices.iloc[position - 1] - 1.0
            strategy_daily.iloc[position] = (1.0 + strategy_daily.iloc[position]) * (
                1.0 + daily_return
            ) - 1.0
        strategy_daily.loc[exit_date] = (1.0 + strategy_daily.loc[exit_date]) * (1.0 - cost) - 1.0

        trades.append(
            {
                "Signal date": signal_date,
                "Probability up": float(probability),
                "Entry date": entry_date,
                "Entry close": entry_price,
                "Exit date": exit_date,
                "Exit close": exit_price,
                "Gross return": gross_return,
                "Net return after costs": net_return,
            }
        )
        next_signal_position = exit_position

    trade_frame = pd.DataFrame(
        trades,
        columns=[
            "Signal date",
            "Probability up",
            "Entry date",
            "Entry close",
            "Exit date",
            "Exit close",
            "Gross return",
            "Net return after costs",
        ],
    )
    first_date = pd.Index(signal_dates)[0]
    evaluation_end = (
        trade_frame["Exit date"].max() if not trade_frame.empty else pd.Index(signal_dates)[-1]
    )
    evaluation_daily = strategy_daily.loc[first_date:evaluation_end]
    strategy_equity = (1.0 + evaluation_daily).cumprod()
    drawdown = strategy_equity / strategy_equity.cummax() - 1.0
    daily_std = float(evaluation_daily.std(ddof=1)) if len(evaluation_daily) > 1 else 0.0
    sharpe = (
        float(np.sqrt(252.0) * evaluation_daily.mean() / daily_std)
        if daily_std > 0
        else float("nan")
    )

    buy_hold_prices = prices.loc[first_date:evaluation_end]
    buy_hold_daily = buy_hold_prices.pct_change(fill_method=None).fillna(0.0)
    buy_hold_equity = (1.0 + buy_hold_daily).cumprod()
    buy_hold_return = float(buy_hold_prices.iloc[-1] / buy_hold_prices.iloc[0] - 1.0)
    buy_hold_return = (1.0 - cost) ** 2 * (1.0 + buy_hold_return) - 1.0

    summary = pd.DataFrame(
        [
            {
                "Strategy": "MLP threshold strategy",
                "Total return": float(strategy_equity.iloc[-1] - 1.0),
                "Maximum drawdown": float(drawdown.min()),
                "Annualized Sharpe": sharpe,
                "Trades": len(trade_frame),
                "Win rate": (
                    float((trade_frame["Net return after costs"] > 0).mean())
                    if not trade_frame.empty
                    else float("nan")
                ),
                "Cost per side (bps)": float(cost_bps_per_side),
                "Threshold": float(threshold),
            },
            {
                "Strategy": "Buy and hold",
                "Total return": buy_hold_return,
                "Maximum drawdown": float((buy_hold_equity / buy_hold_equity.cummax() - 1.0).min()),
                "Annualized Sharpe": (
                    float(np.sqrt(252.0) * buy_hold_daily.mean() / buy_hold_daily.std(ddof=1))
                    if buy_hold_daily.std(ddof=1) > 0
                    else float("nan")
                ),
                "Trades": 1,
                "Win rate": float(buy_hold_return > 0),
                "Cost per side (bps)": float(cost_bps_per_side),
                "Threshold": float("nan"),
            },
        ]
    )
    return summary, trade_frame
