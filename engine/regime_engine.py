"""Regime classification helpers inspired by the book's Chapter 4.

States are +1 bullish, -1 bearish, 0 neutral/insufficient history.
The functions are pure so they can be reused by the NSE/BSE scanner.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def regime_breakout(
    df: pd.DataFrame,
    high_column: str = "High",
    low_column: str = "Low",
    periods: int = 50,
) -> pd.Series:
    """Fresh rolling high -> +1; fresh rolling low -> -1; otherwise carry state."""
    if periods < 2:
        raise ValueError("periods must be at least 2")
    if high_column not in df.columns or low_column not in df.columns:
        raise KeyError(f"Missing required columns: {high_column}, {low_column}")

    highs = pd.to_numeric(df[high_column], errors="coerce")
    lows = pd.to_numeric(df[low_column], errors="coerce")
    states = np.where(
        highs.eq(highs.rolling(periods, min_periods=periods).max()),
        1.0,
        np.where(
            lows.eq(lows.rolling(periods, min_periods=periods).min()),
            -1.0,
            np.nan,
        ),
    )
    return pd.Series(states, index=df.index, name=f"breakout_{periods}").ffill()


def regime_sma(
    df: pd.DataFrame,
    close_column: str = "Close",
    short_period: int = 20,
    long_period: int = 50,
) -> pd.Series:
    """Return the sign of short SMA minus long SMA."""
    _validate_periods(short_period, long_period)
    close = pd.to_numeric(df[close_column], errors="coerce")
    short = close.rolling(short_period, min_periods=short_period).mean()
    long = close.rolling(long_period, min_periods=long_period).mean()
    return pd.Series(np.sign(short - long), index=df.index, name="sma_regime")


def regime_ema(
    df: pd.DataFrame,
    close_column: str = "Close",
    short_period: int = 20,
    long_period: int = 50,
) -> pd.Series:
    """Return the sign of short EMA minus long EMA."""
    _validate_periods(short_period, long_period)
    close = pd.to_numeric(df[close_column], errors="coerce")
    short = close.ewm(span=short_period, min_periods=short_period).mean()
    long = close.ewm(span=long_period, min_periods=long_period).mean()
    return pd.Series(np.sign(short - long), index=df.index, name="ema_regime")


def turtle_trader(
    df: pd.DataFrame,
    high_column: str = "High",
    low_column: str = "Low",
    entry_period: int = 50,
    exit_period: int = 20,
) -> pd.Series:
    """Require slower entry and faster trailing regimes to agree."""
    entry = regime_breakout(df, high_column, low_column, entry_period)
    stop = regime_breakout(df, high_column, low_column, exit_period)
    result = np.where(
        entry.eq(1),
        np.where(stop.eq(1), 1, 0),
        np.where(entry.eq(-1), np.where(stop.eq(-1), -1, 0), 0),
    )
    return pd.Series(result, index=df.index, name="turtle_regime")


def composite_regime_score(*signals: pd.Series) -> pd.Series:
    """Sum aligned directional regime signals (-1/0/+1)."""
    if not signals:
        raise ValueError("At least one regime signal is required")
    frame = pd.concat(signals, axis=1)
    return frame.apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1).rename(
        "regime_score"
    )


def _validate_periods(short_period: int, long_period: int) -> None:
    if short_period < 2 or long_period < 2:
        raise ValueError("moving-average periods must be at least 2")
    if short_period >= long_period:
        raise ValueError("short_period must be less than long_period")
