"""Rule-based intraday setup analysis inspired by the uploaded day-trading books.

The engine deliberately reports observable market structure and setup conditions.
It does not predict profits or guarantee entries.  The first implementation
combines concepts that are directly useful with OHLCV data: price action,
volume, VWAP, 9/20 EMA trend, support/resistance, breakouts/breakdowns, and
opening-range structure.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def _series(frame: pd.DataFrame, name: str) -> pd.Series:
    return pd.to_numeric(frame[name], errors="coerce")


def prepare_day_trading_frame(
    frame: pd.DataFrame,
    vwap_session: bool = True,
) -> pd.DataFrame:
    """Return OHLCV data with a compact set of day-trading indicators."""
    if frame is None or frame.empty:
        return pd.DataFrame()

    data = frame.copy()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(data.columns):
        return pd.DataFrame()

    data = data.dropna(subset=list(required)).sort_index()
    data = data[~data.index.duplicated(keep="last")].copy()
    if data.empty:
        return data

    close = _series(data, "Close")
    high = _series(data, "High")
    low = _series(data, "Low")
    volume = _series(data, "Volume")

    data["EMA 9"] = close.ewm(span=9, adjust=False).mean()
    data["EMA 20"] = close.ewm(span=20, adjust=False).mean()
    data["SMA 50"] = close.rolling(50, min_periods=1).mean()

    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    data["ATR 14"] = true_range.rolling(14, min_periods=1).mean()

    typical = (high + low + close) / 3.0
    if vwap_session:
        session = pd.Series(data.index.date, index=data.index)
        volume_cumulative = volume.groupby(session).cumsum()
        data["VWAP"] = (typical * volume).groupby(session).cumsum() / (
            volume_cumulative.replace(0, float("nan"))
        )
    else:
        data["VWAP"] = (typical * volume).rolling(20, min_periods=1).sum() / (
            volume.rolling(20, min_periods=1).sum().replace(0, float("nan"))
        )

    volume_median = volume.rolling(20, min_periods=5).median().replace(0, float("nan"))
    data["RVOL 20"] = volume / volume_median

    data["Candle body %"] = (
        (close - _series(data, "Open")).abs() / close.replace(0, float("nan")) * 100.0
    )
    data["Bull candle"] = close > _series(data, "Open")
    data["Bear candle"] = close < _series(data, "Open")
    return data


def _opening_range(data: pd.DataFrame, bars: int) -> tuple[float | None, float | None]:
    if bars < 1 or len(data) < bars:
        return None, None
    opening = data.head(bars)
    return float(opening["High"].max()), float(opening["Low"].min())


def analyze_day_trade_setup(
    frame: pd.DataFrame,
    opening_range_bars: int = 1,
    level_lookback: int = 20,
) -> dict[str, Any]:
    """Describe current intraday setup conditions without forecasting."""
    if level_lookback < 2 or opening_range_bars < 1:
        return {}

    data = prepare_day_trading_frame(frame)
    if len(data) < max(5, opening_range_bars + 2):
        return {}

    latest = data.iloc[-1]
    close = float(latest["Close"])
    ema9 = float(latest["EMA 9"])
    ema20 = float(latest["EMA 20"])
    vwap = float(latest["VWAP"])
    rvol = float(latest["RVOL 20"]) if pd.notna(latest["RVOL 20"]) else 0.0
    atr = float(latest["ATR 14"]) if pd.notna(latest["ATR 14"]) else 0.0

    prior = data.iloc[:-1].tail(level_lookback)
    resistance = float(prior["High"].max())
    support = float(prior["Low"].min())
    orb_high, orb_low = _opening_range(data, opening_range_bars)

    bullish_trend = close > vwap and ema9 > ema20
    bearish_trend = close < vwap and ema9 < ema20
    breakout = close > resistance
    breakdown = close < support
    orb_breakout = orb_high is not None and close > orb_high
    orb_breakdown = orb_low is not None and close < orb_low
    volume_confirmed = rvol >= 1.5

    long_points = sum(
        [
            20 if bullish_trend else 0,
            20 if close > vwap else 0,
            15 if ema9 > ema20 else 0,
            15 if breakout else 0,
            15 if orb_breakout else 0,
            15 if volume_confirmed else 0,
        ]
    )
    short_points = sum(
        [
            20 if bearish_trend else 0,
            20 if close < vwap else 0,
            15 if ema9 < ema20 else 0,
            15 if breakdown else 0,
            15 if orb_breakdown else 0,
            15 if volume_confirmed else 0,
        ]
    )

    if long_points >= 70 and long_points > short_points:
        setup = "LONG SETUP WATCH"
    elif short_points >= 70 and short_points > long_points:
        setup = "SHORT SETUP WATCH"
    elif bullish_trend or bearish_trend:
        setup = "TREND WATCH"
    elif breakout or breakdown:
        setup = "BREAKOUT/BREAKDOWN WATCH"
    else:
        setup = "NO CLEAR SETUP"

    return {
        "Setup": setup,
        "Long setup score": long_points,
        "Short setup score": short_points,
        "Trend": ("UPTREND" if bullish_trend else "DOWNTREND" if bearish_trend else "MIXED"),
        "VWAP relation": "ABOVE" if close > vwap else "BELOW",
        "EMA 9/20": "BULLISH" if ema9 > ema20 else "BEARISH",
        "RVOL": round(rvol, 2),
        "Volume confirmation": "YES" if volume_confirmed else "NO",
        "Support": round(support, 2),
        "Resistance": round(resistance, 2),
        "ORB high": None if orb_high is None else round(orb_high, 2),
        "ORB low": None if orb_low is None else round(orb_low, 2),
        "Breakout": "YES" if breakout else "NO",
        "Breakdown": "YES" if breakdown else "NO",
        "ATR 14": round(atr, 2),
        "Close": round(close, 2),
    }


def calculate_day_trade_plan(strategy: dict[str, Any]) -> dict[str, Any]:
    """Calculate conditional entry, stop and target reference levels."""
    close = float(strategy.get("Close", 0) or 0)
    atr = float(strategy.get("ATR 14", 0) or 0)
    support = strategy.get("Support")
    resistance = strategy.get("Resistance")
    direction = (
        "LONG"
        if strategy.get("Long setup score", 0) > strategy.get("Short setup score", 0)
        else (
            "SHORT"
            if strategy.get("Short setup score", 0) > strategy.get("Long setup score", 0)
            else "NEUTRAL"
        )
    )

    if close <= 0 or atr <= 0:
        return {
            "Plan": "INSUFFICIENT DATA",
            "Entry reference": None,
            "Stop reference": None,
            "Target 1": None,
            "Target 2": None,
            "Target 3": None,
            "Risk per share": None,
            "R:R T1": None,
            "R:R T2": None,
            "R:R T3": None,
        }

    if direction == "LONG":
        entry = float(resistance) if resistance is not None else close
        stop = min(close - atr, float(support)) if support is not None else close - atr
        if entry <= stop:
            entry = close
            stop = close - atr
    elif direction == "SHORT":
        entry = float(support) if support is not None else close
        stop = max(close + atr, float(resistance)) if resistance is not None else close + atr
        if entry >= stop:
            entry = close
            stop = close + atr
    else:
        return {
            "Plan": "NO CLEAR DIRECTION",
            "Entry reference": None,
            "Stop reference": None,
            "Target 1": None,
            "Target 2": None,
            "Target 3": None,
            "Risk per share": None,
            "R:R T1": None,
            "R:R T2": None,
            "R:R T3": None,
        }

    risk = abs(entry - stop)
    if risk <= 0:
        return {
            "Plan": "INSUFFICIENT RISK RANGE",
            "Entry reference": round(entry, 2),
            "Stop reference": round(stop, 2),
            "Target 1": None,
            "Target 2": None,
            "Target 3": None,
            "Risk per share": None,
            "R:R T1": None,
            "R:R T2": None,
            "R:R T3": None,
        }

    targets = [
        entry + risk * multiple if direction == "LONG" else entry - risk * multiple
        for multiple in (1.0, 2.0, 3.0)
    ]
    return {
        "Plan": f"{direction} reference plan",
        "Entry reference": round(entry, 2),
        "Stop reference": round(stop, 2),
        "Target 1": round(targets[0], 2),
        "Target 2": round(targets[1], 2),
        "Target 3": round(targets[2], 2),
        "Risk per share": round(risk, 2),
        "R:R T1": 1.0,
        "R:R T2": 2.0,
        "R:R T3": 3.0,
    }


def classify_day_trade_plan_state(strategy: dict[str, Any], plan: dict[str, Any]) -> str:
    """Classify the current setup against its reference levels."""
    if not plan.get("Entry reference") or not plan.get("Stop reference"):
        return "NO TRADE PLAN"

    close = float(strategy.get("Close", 0) or 0)
    entry = float(plan["Entry reference"])
    stop = float(plan["Stop reference"])
    direction = "LONG" if "LONG" in str(plan.get("Plan", "")) else "SHORT"

    if close <= 0:
        return "NO TRADE PLAN"

    if direction == "LONG":
        if close <= stop:
            return "INVALIDATED"
        if close >= entry:
            return "TRIGGERED / ABOVE REFERENCE"
        return "WAITING FOR REFERENCE"
    if close >= stop:
        return "INVALIDATED"
    if close <= entry:
        return "TRIGGERED / BELOW REFERENCE"
    return "WAITING FOR REFERENCE"


def analyze_narrow_range_breakout(
    frame: pd.DataFrame,
    lookback: int = 4,
    trend_lookback: int = 20,
    atr_window: int = 14,
    max_range_atr: float = 0.67,
) -> dict[str, Any]:
    """Identify a completed narrow-range setup and its next-bar trigger levels.

    NR4/NR7 means the latest completed candle has the smallest high-low range
    among the last N completed candles. The setup is only a watch condition:
    a subsequent bar must break the setup high/low to trigger. No future bars
    are used in detection.
    """
    if lookback not in (4, 7) or trend_lookback < 2 or atr_window < 2:
        return {}
    if not 0 < max_range_atr <= 1:
        return {}
    data = prepare_day_trading_frame(frame)
    required = {"Open", "High", "Low", "Close", "Volume"}
    if data.empty or not required.issubset(data.columns):
        return {}
    if len(data) < max(lookback, trend_lookback, atr_window) + 1:
        return {}

    high = pd.to_numeric(data["High"], errors="coerce")
    low = pd.to_numeric(data["Low"], errors="coerce")
    close = pd.to_numeric(data["Close"], errors="coerce")
    ranges = high - low
    setup_range = float(ranges.iloc[-1])
    comparison = ranges.iloc[-lookback:]
    if comparison.isna().any() or setup_range <= 0:
        return {}
    is_narrowest = setup_range <= float(comparison.min())
    atr = float(data["ATR 14"].iloc[-1])
    if not pd.notna(atr) or atr <= 0:
        true_range = pd.concat(
            [high - low, (high - close.shift()).abs(), (low - close.shift()).abs()],
            axis=1,
        ).max(axis=1)
        atr = float(true_range.rolling(atr_window, min_periods=atr_window).mean().iloc[-1])
    if not pd.notna(atr) or atr <= 0:
        return {}

    setup_high = float(high.iloc[-1])
    setup_low = float(low.iloc[-1])
    narrow_by_atr = setup_range / atr <= max_range_atr
    prior_trend = close.iloc[-trend_lookback - 1 : -1]
    prior_mean = float(prior_trend.mean()) if len(prior_trend) else float("nan")
    trend = (
        "UPTREND"
        if close.iloc[-2] > prior_mean
        else "DOWNTREND"
        if close.iloc[-2] < prior_mean
        else "MIXED"
    )
    qualifies = is_narrowest and narrow_by_atr
    pattern = f"NR{lookback}" if qualifies else "NO NARROW-RANGE SETUP"

    return {
        "Pattern": pattern,
        "Qualifies": bool(qualifies),
        "Narrowest in lookback": bool(is_narrowest),
        "Range/ATR": round(setup_range / atr, 4),
        "ATR": round(atr, 4),
        "Setup high": round(setup_high, 4),
        "Setup low": round(setup_low, 4),
        "Long trigger": round(setup_high, 4) if qualifies else None,
        "Short trigger": round(setup_low, 4) if qualifies else None,
        "Long stop reference": round(setup_low, 4) if qualifies else None,
        "Short stop reference": round(setup_high, 4) if qualifies else None,
        "Trend context": trend,
        "Signal timing": "NEXT BAR BREAK ONLY",
    }


def classify_narrow_range_breakout(
    setup: dict[str, Any],
    next_bar_high: float,
    next_bar_low: float,
) -> str:
    """Classify a next-bar range break; simultaneous breaks are ambiguous."""
    if not setup.get("Qualifies"):
        return "NO VALID SETUP"
    try:
        high = float(next_bar_high)
        low = float(next_bar_low)
        long_trigger = float(setup["Long trigger"])
        short_trigger = float(setup["Short trigger"])
    except (TypeError, ValueError, KeyError):
        return "INVALID BAR"
    if high < low:
        return "INVALID BAR"
    long_break = high > long_trigger
    short_break = low < short_trigger
    if long_break and short_break:
        return "AMBIGUOUS — BOTH SIDES TOUCHED"
    if long_break:
        return "LONG BREAKOUT"
    if short_break:
        return "SHORT BREAKDOWN"
    return "WAITING"
