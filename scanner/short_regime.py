from __future__ import annotations

import pandas as pd


def regime_breakdown(
    df: pd.DataFrame,
    high_lookback: int = 50,
    low_lookback: int = 50,
) -> pd.Series:
    """Classify each bar from fresh highs/lows over prior rolling windows.

    A fresh high is classified as bullish, a fresh low as bearish, and all
    other observations as neutral. The current bar is compared with prior
    observations only, avoiding look-ahead from the current bar.
    """
    if high_lookback < 1 or low_lookback < 1:
        raise ValueError("lookback windows must be positive")

    required = {"High", "Low"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    highs = pd.to_numeric(df["High"], errors="coerce")
    lows = pd.to_numeric(df["Low"], errors="coerce")

    prior_high = highs.shift(1).rolling(high_lookback, min_periods=high_lookback).max()
    prior_low = lows.shift(1).rolling(low_lookback, min_periods=low_lookback).min()

    regime = pd.Series("NEUTRAL", index=df.index, dtype="string")
    regime.loc[highs > prior_high] = "BULLISH"
    regime.loc[lows < prior_low] = "BEARISH"

    return regime


def turtle_regime(
    df: pd.DataFrame,
    entry_lookback: int = 50,
    exit_lookback: int = 20,
) -> pd.Series:
    """Classify a simplified Turtle regime using asymmetric breakouts.

    The longer entry window establishes direction. The shorter exit window
    acts as the faster confirmation/stop regime. A signal is emitted only
    when both regimes agree; disagreement is neutral. This mirrors the
    Chapter 4 simplified Turtle construction while keeping the implementation
    free of look-ahead by delegating to :func:`regime_breakdown`.
    """
    if entry_lookback < 1 or exit_lookback < 1:
        raise ValueError("lookback windows must be positive")

    entry_regime = regime_breakdown(
        df,
        high_lookback=entry_lookback,
        low_lookback=entry_lookback,
    )
    exit_regime = regime_breakdown(
        df,
        high_lookback=exit_lookback,
        low_lookback=exit_lookback,
    )

    turtle = pd.Series("NEUTRAL", index=df.index, dtype="string")
    bullish = (entry_regime == "BULLISH") & (exit_regime == "BULLISH")
    bearish = (entry_regime == "BEARISH") & (exit_regime == "BEARISH")
    turtle.loc[bullish] = "BULLISH"
    turtle.loc[bearish] = "BEARISH"
    return turtle
