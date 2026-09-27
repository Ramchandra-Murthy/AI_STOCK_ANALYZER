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
