"""Technical indicator scoring service.

Calculates a bounded 0-100 technical component score from the canonical
technical-data frame. This module owns technical scoring only; recommendation
and portfolio-level decisions remain in their respective services.
"""

from __future__ import annotations

import math


def _valid_number(value) -> bool:
    """Return True when value is a finite usable numeric value."""
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def calculate_technical_score(df):
    """Calculate a technical score and the observations supporting it.

    A score is only produced when at least one supported technical indicator is
    actually available. Missing indicator evidence is never converted into the
    neutral baseline score of 50.
    """
    if df is None or getattr(df, "empty", True):
        return None, ["Historical price data is unavailable"]

    score = 50
    reasons = []
    observed_components = 0
    latest = df.iloc[-1]

    # RSI must be inside its valid indicator domain.
    if "RSI" in latest.index and _valid_number(latest["RSI"]):
        rsi = float(latest["RSI"])
        if 0.0 <= rsi <= 100.0:
            observed_components += 1
            if rsi < 30:
                score += 15
                reasons.append(f"RSI is oversold at {rsi:.1f}")
            elif rsi > 70:
                score -= 15
                reasons.append(f"RSI is overbought at {rsi:.1f}")
            else:
                score += 5
                reasons.append(f"RSI is neutral at {rsi:.1f}")
        else:
            reasons.append("RSI data is outside the valid 0-100 range")
    else:
        reasons.append("RSI data is unavailable")

    # EMA20 vs EMA50
    if (
        "EMA20" in latest.index
        and "EMA50" in latest.index
        and _valid_number(latest["EMA20"])
        and _valid_number(latest["EMA50"])
    ):
        observed_components += 1
        ema20 = float(latest["EMA20"])
        ema50 = float(latest["EMA50"])
        if ema20 > ema50:
            score += 10
            reasons.append(
                "EMA20 is above EMA50, indicating short-term bullish momentum"
            )
        elif ema20 < ema50:
            score -= 5
            reasons.append(
                "EMA20 is below EMA50, indicating short-term weakness"
            )
        else:
            reasons.append("EMA20 is equal to EMA50")

    # EMA50 vs EMA200
    if (
        "EMA50" in latest.index
        and "EMA200" in latest.index
        and _valid_number(latest["EMA50"])
        and _valid_number(latest["EMA200"])
    ):
        observed_components += 1
        ema50 = float(latest["EMA50"])
        ema200 = float(latest["EMA200"])
        if ema50 > ema200:
            score += 10
            reasons.append(
                "EMA50 is above EMA200, indicating a bullish long-term trend"
            )
        elif ema50 < ema200:
            score -= 10
            reasons.append(
                "EMA50 is below EMA200, indicating a bearish long-term trend"
            )
        else:
            reasons.append("EMA50 is equal to EMA200")

    # MACD
    if (
        "MACD" in latest.index
        and "MACD_Signal" in latest.index
        and _valid_number(latest["MACD"])
        and _valid_number(latest["MACD_Signal"])
    ):
        observed_components += 1
        macd = float(latest["MACD"])
        macd_signal = float(latest["MACD_Signal"])
        if macd > macd_signal:
            score += 10
            reasons.append(
                "MACD is above its signal line, indicating bullish momentum"
            )
        elif macd < macd_signal:
            score -= 10
            reasons.append(
                "MACD is below its signal line, indicating bearish momentum"
            )
        else:
            reasons.append("MACD is equal to its signal line")
    else:
        reasons.append("MACD data is unavailable")

    # Breakout / resistance
    if (
        "Close" in latest.index
        and "Resistance" in latest.index
        and _valid_number(latest["Close"])
        and _valid_number(latest["Resistance"])
    ):
        observed_components += 1
        close = float(latest["Close"])
        resistance = float(latest["Resistance"])
        if close > resistance:
            score += 10
            reasons.append("Price has broken above resistance")
        else:
            reasons.append("Price remains below resistance")

    # Support
    if (
        "Close" in latest.index
        and "Support" in latest.index
        and _valid_number(latest["Close"])
        and _valid_number(latest["Support"])
    ):
        observed_components += 1
        close = float(latest["Close"])
        support = float(latest["Support"])
        if close > support:
            score += 5
            reasons.append("Price is trading above support")
        elif close < support:
            score -= 10
            reasons.append("Price is trading below support")
        else:
            reasons.append("Price is trading at support")

    if observed_components == 0:
        return None, ["Insufficient technical indicators for scoring"]

    score = max(0, min(round(score), 100))

    return score, reasons
