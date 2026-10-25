from __future__ import annotations

import math
from typing import Any

import pandas as pd

_REQUIRED_COLUMNS = ("SMA_20", "SMA_50", "EMA_20", "RSI_14", "MACD", "Signal", "Close")


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _recommendation_for_score(score: int) -> str:
    """Map the technical score to a label without implying predictive probability."""
    if score >= 85:
        return "STRONG BUY"
    if score >= 70:
        return "BUY"
    if score >= 45:
        return "HOLD"
    if score >= 25:
        return "SELL"
    return "STRONG SELL"


def generate_signal(df: pd.DataFrame) -> dict[str, Any]:
    """Generate a deterministic technical signal from the supplied indicator frame.

    Live/latest market observations deliberately do not enter this engine. They belong
    to the canonical market service so historical analysis remains reproducible.
    The technical score is not a calibrated probability of success, so confidence is
    deliberately reported as unavailable until validated out-of-sample calibration exists.
    """
    if df is None or df.empty:
        return {"Status": "ERROR", "Message": "No indicator data available."}
    missing = [c for c in _REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return {"Status": "ERROR", "Message": f"Missing required indicator: {missing[0]}"}
    last = df.iloc[-1]
    values = {c: _finite(last[c]) for c in _REQUIRED_COLUMNS}
    invalid = [c for c, v in values.items() if v is None]
    if invalid:
        return {"Status": "ERROR", "Message": f"Invalid indicator value: {invalid[0]}"}

    score = 50
    components: dict[str, int] = {"Base": 50}
    reasons: list[str] = []
    risk = "Medium"
    if values["SMA_20"] > values["SMA_50"]:
        score += 15
        components["SMA trend"] = 15
        reasons.append("20 SMA above 50 SMA (Bullish)")
    else:
        score -= 15
        components["SMA trend"] = -15
        reasons.append("20 SMA below 50 SMA (Bearish)")
    if values["EMA_20"] > values["SMA_20"]:
        score += 10
        components["EMA trend"] = 10
        reasons.append("EMA20 above SMA20")
    else:
        score -= 10
        components["EMA trend"] = -10
        reasons.append("EMA20 below SMA20")

    rsi = values["RSI_14"]
    if rsi < 30:
        components["RSI"] = 20
        score += 20
        reasons.append("RSI Oversold")
    elif rsi <= 45:
        components["RSI"] = 10
        score += 10
        reasons.append("RSI Bullish Zone")
    elif rsi < 60:
        components["RSI"] = 5
        score += 5
        reasons.append("RSI Neutral")
    elif rsi < 70:
        components["RSI"] = -5
        score -= 5
        reasons.append("RSI Slightly Overbought")
    else:
        components["RSI"] = -20
        score -= 20
        reasons.append("RSI Overbought")

    if values["MACD"] > values["Signal"]:
        components["MACD"] = 15
        score += 15
        reasons.append("MACD Bullish Crossover")
    else:
        components["MACD"] = -15
        score -= 15
        reasons.append("MACD Bearish Crossover")

    close = values["Close"]
    lower = _finite(last["BB_Lower"]) if "BB_Lower" in last.index else None
    upper = _finite(last["BB_Upper"]) if "BB_Upper" in last.index else None
    components["Bollinger"] = 0
    if lower is not None and close < lower:
        components["Bollinger"] = 10
        score += 10
        reasons.append("Price below Lower Bollinger Band")
    elif upper is not None and close > upper:
        components["Bollinger"] = -10
        score -= 10
        reasons.append("Price above Upper Bollinger Band")

    support = _finite(last["Support"]) if "Support" in last.index else None
    resistance = _finite(last["Resistance"]) if "Resistance" in last.index else None
    components["Support"] = 0
    if support is not None and close <= support * 1.02:
        components["Support"] = 10
        score += 10
        reasons.append("Trading near Support")
    components["Resistance"] = 0
    if resistance is not None and close >= resistance * 0.98:
        components["Resistance"] = -10
        score -= 10
        reasons.append("Trading near Resistance")

    atr = _finite(last["ATR"]) if "ATR" in last.index else None
    components["Volatility"] = 0
    if atr is not None and atr >= 0 and close > 0:
        atr_percent = atr / close * 100
        if atr_percent > 5:
            risk = "High"
            components["Volatility"] = -5
            score -= 5
            reasons.append("High Volatility")
        elif atr_percent < 2:
            risk = "Low"
            components["Volatility"] = 5
            score += 5
            reasons.append("Low Volatility")

    score = max(0, min(int(score), 100))
    recommendation = _recommendation_for_score(score)
    return {
        "Status": "OK",
        "Score": score,
        "Score Components": components,
        "Confidence": None,
        "Confidence Status": "Not calibrated",
        "Recommendation": recommendation,
        "Risk": risk,
        "Reasons": reasons,
    }
