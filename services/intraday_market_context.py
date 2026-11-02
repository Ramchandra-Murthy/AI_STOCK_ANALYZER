"""Pure intraday market-context metrics for explainable Stocks-in-Play screening.

This module computes descriptive context only. It does not generate trade signals.
"""

import math
import pandas as pd
from typing import Any


_REQUIRED = {"Open", "High", "Low", "Close", "Volume"}


def intraday_market_context(
    intraday: pd.DataFrame,
    *,
    previous_close: float | None = None,
    average_daily_volume: float | None = None,
    average_daily_turnover: float | None = None,
) -> dict[str, Any]:
    """Summarize current-session gap, move, relative volume and liquidity context.

    intraday must contain OHLCV candles for a single session. Relative volume
    is cumulative session volume divided by average daily volume; it is not
    time-of-day-normalized RVOL. Missing or invalid baselines return None.
    """
    if intraday is None or intraday.empty or not _REQUIRED.issubset(intraday.columns):
        return {}

    data = intraday.loc[:, list(_REQUIRED)].copy()
    data = data.apply(pd.to_numeric, errors="coerce")
    data = data.replace([float("inf"), float("-inf")], float("nan"))
    data = data.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
    if data.empty:
        return {}

    valid = (
        (data[["Open", "High", "Low", "Close"]] > 0).all(axis=1)
        & (data["Volume"] >= 0)
        & (data["High"] >= data[["Open", "Close", "Low"]].max(axis=1))
        & (data["Low"] <= data[["Open", "Close", "High"]].min(axis=1))
    )
    data = data.loc[valid].sort_index()
    if data.empty:
        return {}

    first_open = float(data["Open"].iloc[0])
    last_close = float(data["Close"].iloc[-1])
    cumulative_volume = float(data["Volume"].sum())
    cumulative_turnover = float((data["Close"] * data["Volume"]).sum())

    prev_close = _positive_finite(previous_close)
    avg_volume = _positive_finite(average_daily_volume)
    avg_turnover = _positive_finite(average_daily_turnover)

    return {
        "Previous close": prev_close,
        "Gap %": _percent(first_open, prev_close),
        "Last price": last_close,
        "Intraday change %": _percent(last_close, first_open),
        "Session volume": int(cumulative_volume),
        "Cumulative RVOL": (
            round(cumulative_volume / avg_volume, 3) if avg_volume is not None else None
        ),
        "Session turnover": round(cumulative_turnover, 2),
        "Average daily turnover": avg_turnover,
        "Turnover ratio": (
            round(cumulative_turnover / avg_turnover, 3) if avg_turnover is not None else None
        ),
        "Context status": "OK",
    }


def _positive_finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def _percent(value: float, base: float | None) -> float | None:
    if base is None or base <= 0:
        return None
    return round((value - base) / base * 100.0, 3)
