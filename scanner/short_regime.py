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


def moving_average_regime(
    df: pd.DataFrame,
    fast_window: int = 20,
    slow_window: int = 50,
    price_column: str = "Close",
) -> pd.Series:
    """Classify regime from a fast/slow moving-average crossover.

    A fast moving average above the slow moving average is bullish, below it
    is bearish, and equality is neutral. Rolling windows use only observations
    available at each bar, so the regime does not introduce look-ahead.
    """
    if fast_window < 1 or slow_window < 1:
        raise ValueError("moving-average windows must be positive")
    if fast_window >= slow_window:
        raise ValueError("fast_window must be smaller than slow_window")
    if price_column not in df.columns:
        raise ValueError(f"missing required column: {price_column}")

    prices = pd.to_numeric(df[price_column], errors="coerce")
    fast_ma = prices.rolling(fast_window, min_periods=fast_window).mean()
    slow_ma = prices.rolling(slow_window, min_periods=slow_window).mean()

    regime = pd.Series("NEUTRAL", index=df.index, dtype="string")
    regime.loc[fast_ma > slow_ma] = "BULLISH"
    regime.loc[fast_ma < slow_ma] = "BEARISH"
    return regime


def fractal_swings(
    df: pd.DataFrame,
    levels: int = 3,
) -> pd.DataFrame:
    """Calculate recursive fractal swing highs and lows.

    The Chapter 4 construction uses the average of High, Low, and Close as
    the source series. Level 1 identifies local swings from adjacent bars;
    each higher level identifies swings from the preceding level's swings.
    The returned columns are sparse swing-price series indexed like the input.
    """
    if levels < 1:
        raise ValueError("levels must be positive")
    required = {"High", "Low", "Close"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    source = df[["High", "Low", "Close"]].apply(
        pd.to_numeric, errors="coerce"
    ).mean(axis=1)
    result = pd.DataFrame(index=df.index)

    current = source.dropna()
    for level in range(1, levels + 1):
        if len(current) < 3:
            break

        previous = current.shift(1)
        following = current.shift(-1)
        lows = current[(current <= previous) & (current < following)]
        highs = current[(current >= previous) & (current > following)]

        result[f"Lo{level}"] = lows.reindex(df.index)
        result[f"Hi{level}"] = highs.reindex(df.index)

        swings = pd.concat(
            [lows.rename("value"), highs.rename("value")]
        ).sort_index()
        swings = swings[~swings.index.duplicated(keep="first")]
        current = swings

    return result
