"""Chapter 4-style multi-method market regime engine.

The book's regime chapter describes breakout/breakdown, Turtle traders, moving-average
crossovers, fractals, higher highs/lows, floor/ceiling and a composite score, with the
methodology applied across multiple timeframes. This module provides a deterministic,
look-ahead-aware implementation of those named methods for OHLC data.

The exact parameter choices below are application defaults, not claims that the book
mandates these values. They are exposed as arguments so they can be backtested.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


SCORE_COLUMNS = [
    "Breakout score",
    "Turtle score",
    "MA crossover score",
    "Fractal score",
    "HH/HL score",
    "Floor/Ceiling score",
]


def calculate_regime_indicators(
    frame: pd.DataFrame | None,
    *,
    breakout_window: int = 20,
    turtle_window: int = 55,
    fast_ma: int = 10,
    slow_ma: int = 30,
    fractal_window: int = 2,
    structure_window: int = 5,
    level_window: int = 20,
) -> pd.DataFrame:
    """Calculate Chapter 4-style regime indicators without future-data leakage."""
    data = _normalise_ohlc(frame)
    if data.empty:
        return pd.DataFrame(columns=_output_columns())

    for value in (
        breakout_window,
        turtle_window,
        fast_ma,
        slow_ma,
        fractal_window,
        structure_window,
        level_window,
    ):
        if int(value) < 1:
            raise ValueError("Regime windows must be positive integers.")

    close = data["Close"]
    high = data["High"]
    low = data["Low"]

    breakout_high = high.shift(1).rolling(breakout_window, min_periods=breakout_window).max()
    breakout_low = low.shift(1).rolling(breakout_window, min_periods=breakout_window).min()
    data["Breakout score"] = _direction_score(close, breakout_high, breakout_low)

    turtle_high = high.shift(1).rolling(turtle_window, min_periods=turtle_window).max()
    turtle_low = low.shift(1).rolling(turtle_window, min_periods=turtle_window).min()
    data["Turtle score"] = _direction_score(close, turtle_high, turtle_low)

    fast = close.rolling(fast_ma, min_periods=fast_ma).mean()
    slow = close.rolling(slow_ma, min_periods=slow_ma).mean()
    data["MA crossover score"] = _comparison_score(fast, slow)

    data["Fractal score"] = _fractal_score(high, low, fractal_window)

    prior_high = high.shift(1).rolling(
        structure_window, min_periods=structure_window
    ).max()
    prior_low = low.shift(1).rolling(
        structure_window, min_periods=structure_window
    ).min()
    higher_high = high > prior_high
    lower_low = low < prior_low
    higher_low = low > low.shift(structure_window)
    lower_high = high < high.shift(structure_window)
    data["HH/HL score"] = 0
    data.loc[higher_high & higher_low, "HH/HL score"] = 1
    data.loc[lower_low & lower_high, "HH/HL score"] = -1
    data.loc[prior_high.isna() | prior_low.isna(), "HH/HL score"] = pd.NA
    data["HH/HL score"] = data["HH/HL score"].astype("Int64")

    ceiling = high.shift(1).rolling(level_window, min_periods=level_window).max()
    floor = low.shift(1).rolling(level_window, min_periods=level_window).min()
    data["Floor/Ceiling score"] = _direction_score(close, ceiling, floor)

    data["Composite score"] = data[SCORE_COLUMNS].sum(axis=1, min_count=1)
    data["Composite score"] = data["Composite score"].where(
        data[SCORE_COLUMNS].notna().all(axis=1)
    )
    data["Regime"] = data["Composite score"].map(classify_regime)
    return data[_output_columns()]


def classify_regime(score: float | int | None, threshold: int = 2) -> str:
    """Convert a composite score into a descriptive regime bucket."""
    if score is None or pd.isna(score):
        return "INSUFFICIENT DATA"
    threshold = max(1, int(threshold))
    if score >= threshold:
        return "BULLISH"
    if score <= -threshold:
        return "BEARISH"
    return "RANGE / MIXED"


def latest_regime(
    frame: pd.DataFrame | None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Return the latest completed-bar regime snapshot."""
    result = calculate_regime_indicators(frame, **kwargs)
    if result.empty:
        return {}
    row = result.iloc[-1]
    return {key: row[key] for key in result.columns}


def multi_timeframe_regime(
    frames: dict[str, pd.DataFrame | None],
    *,
    weights: dict[str, float] | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Summarise the latest regime across supplied timeframes."""
    rows: list[dict[str, Any]] = []
    for timeframe, frame in frames.items():
        snapshot = latest_regime(frame, **kwargs)
        if not snapshot:
            continue
        score = snapshot.get("Composite score")
        weight = float(weights.get(timeframe, 1.0)) if weights else 1.0
        rows.append(
            {
                "Timeframe": timeframe,
                "Regime": snapshot.get("Regime", "INSUFFICIENT DATA"),
                "Composite score": score,
                "Weight": weight,
            }
        )

    result = pd.DataFrame(rows)
    if result.empty:
        return pd.DataFrame(
            columns=["Timeframe", "Regime", "Composite score", "Weight"]
        )

    numeric_scores = pd.to_numeric(result["Composite score"], errors="coerce")
    valid = numeric_scores.notna() & result["Weight"].gt(0)
    if valid.any():
        result.attrs["weighted_composite_score"] = float(
            (numeric_scores[valid] * result.loc[valid, "Weight"]).sum()
            / result.loc[valid, "Weight"].sum()
        )
    else:
        result.attrs["weighted_composite_score"] = None
    return result


def relative_regime(
    frame: pd.DataFrame | None,
    benchmark_close: pd.Series | None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Apply the same regime framework to price relative to a benchmark."""
    data = _normalise_ohlc(frame)
    if data.empty or benchmark_close is None:
        return pd.DataFrame(columns=_output_columns())

    benchmark = pd.to_numeric(
        pd.Series(benchmark_close, index=benchmark_close.index), errors="coerce"
    )
    relative = data["Close"].div(benchmark.reindex(data.index))
    relative = relative.replace([float("inf"), float("-inf")], pd.NA).dropna()
    if relative.empty:
        return pd.DataFrame(columns=_output_columns())

    synthetic = pd.DataFrame(
        {
            "Open": relative,
            "High": relative,
            "Low": relative,
            "Close": relative,
            "Volume": 0.0,
        },
        index=relative.index,
    )
    return calculate_regime_indicators(synthetic, **kwargs)


def _normalise_ohlc(frame: pd.DataFrame | None) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

    data = frame.copy()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    required = {"High", "Low", "Close"}
    if not required.issubset(data.columns):
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

    for column in ("High", "Low", "Close"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=["High", "Low", "Close"])
    return data.sort_index()


def _direction_score(
    close: pd.Series,
    upper: pd.Series,
    lower: pd.Series,
) -> pd.Series:
    score = pd.Series(0, index=close.index, dtype="int64")
    score.loc[close > upper] = 1
    score.loc[close < lower] = -1
    score.loc[upper.isna() | lower.isna()] = pd.NA
    return score.astype("Int64")


def _comparison_score(left: pd.Series, right: pd.Series) -> pd.Series:
    score = pd.Series(0, index=left.index, dtype="int64")
    score.loc[left > right] = 1
    score.loc[left < right] = -1
    score.loc[left.isna() | right.isna()] = pd.NA
    return score.astype("Int64")


def _fractal_score(
    high: pd.Series,
    low: pd.Series,
    window: int,
) -> pd.Series:
    width = 2 * window + 1
    highest = high.eq(high.rolling(width, center=True, min_periods=width).max())
    lowest = low.eq(low.rolling(width, center=True, min_periods=width).min())

    # A fractal is only usable after the right-hand confirmation bars have completed.
    bearish = highest.shift(window, fill_value=False)
    bullish = lowest.shift(window, fill_value=False)

    score = pd.Series(0, index=high.index, dtype="int64")
    score.loc[bullish & ~bearish] = 1
    score.loc[bearish & ~bullish] = -1
    score.loc[highest.isna() | lowest.isna()] = pd.NA
    return score.astype("Int64")


def _output_columns() -> list[str]:
    return ["Close", *SCORE_COLUMNS, "Composite score", "Regime"]
