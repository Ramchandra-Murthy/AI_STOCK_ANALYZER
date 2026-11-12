"""Shared validation for provider-supplied intraday OHLCV candles."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from services.market_calendar import (
    CalendarUnavailableError,
    equity_market_session_status,
    is_equity_trading_day,
)

IST = ZoneInfo("Asia/Kolkata")
OHLCV_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


def completed_ohlcv_bars(
    frame: pd.DataFrame,
    as_of: datetime,
    interval_minutes: int,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Normalize timestamps and keep only complete, unique, physically valid bars."""
    rejected = {
        "invalid_timestamps": 0,
        "future_candles": 0,
        "incomplete_candles": 0,
        "duplicate_candles": 0,
        "missing_ohlcv": 0,
        "invalid_ohlcv": 0,
        "missing_ohlcv_columns": 0,
    }
    if frame.empty:
        return frame, rejected
    if not set(OHLCV_COLUMNS).issubset(frame.columns):
        rejected["missing_ohlcv_columns"] = 1
        return pd.DataFrame(columns=OHLCV_COLUMNS), rejected

    current = pd.Timestamp(as_of)
    current = current.tz_localize(IST) if current.tzinfo is None else current.tz_convert(IST)
    records: dict[pd.Timestamp, dict[str, float]] = {}
    for timestamp, row in frame.iterrows():
        try:
            start = pd.Timestamp(timestamp)
            if pd.isna(start):
                raise ValueError("invalid timestamp")
            start = start.tz_localize(IST) if start.tzinfo is None else start.tz_convert(IST)
        except (TypeError, ValueError, OverflowError):
            rejected["invalid_timestamps"] += 1
            continue
        if start > current:
            rejected["future_candles"] += 1
            continue
        if start + pd.Timedelta(minutes=interval_minutes) > current:
            rejected["incomplete_candles"] += 1
            continue
        if row.loc[list(OHLCV_COLUMNS)].isna().any():
            rejected["missing_ohlcv"] += 1
            continue
        try:
            candle = {name: float(row[name]) for name in OHLCV_COLUMNS}
        except (TypeError, ValueError, OverflowError):
            rejected["invalid_ohlcv"] += 1
            continue
        if (
            not all(pd.notna(value) and abs(value) != float("inf") for value in candle.values())
            or min(candle[name] for name in OHLCV_COLUMNS[:4]) <= 0
            or candle["Volume"] < 0
            or candle["High"] < max(candle["Open"], candle["Close"], candle["Low"])
            or candle["Low"] > min(candle["Open"], candle["Close"], candle["High"])
        ):
            rejected["invalid_ohlcv"] += 1
            continue
        if start in records:
            rejected["duplicate_candles"] += 1
        records[start] = candle

    completed = pd.DataFrame.from_dict(records, orient="index", columns=OHLCV_COLUMNS)
    completed.index = pd.DatetimeIndex(completed.index)
    return completed.sort_index(), rejected


def current_session_ohlcv_bars(
    frame: pd.DataFrame,
    as_of: datetime,
    interval_minutes: int,
    stale_after_minutes: int = 15,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Keep valid completed bars from today, rejecting stale or unverified sessions."""
    completed, rejected = completed_ohlcv_bars(frame, as_of, interval_minutes)
    rejected["stale_symbols"] = 0
    if completed.empty:
        return completed, rejected

    current = pd.Timestamp(as_of)
    current = current.tz_localize(IST) if current.tzinfo is None else current.tz_convert(IST)
    session_status = equity_market_session_status(current.to_pydatetime())
    try:
        trading_day = is_equity_trading_day(current.date())
    except CalendarUnavailableError:
        trading_day = False

    latest_end = completed.index[-1] + pd.Timedelta(minutes=interval_minutes)
    is_stale_open_candle = (
        session_status == "OPEN"
        and (current - latest_end).total_seconds() > stale_after_minutes * 60
    )
    if (
        session_status == "CALENDAR_UNAVAILABLE"
        or not trading_day
        or completed.index[-1].date() != current.date()
        or is_stale_open_candle
    ):
        rejected["stale_symbols"] = 1
        return completed.iloc[0:0], rejected
    return completed, rejected
