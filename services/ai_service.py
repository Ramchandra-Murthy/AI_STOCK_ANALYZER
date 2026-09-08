"""AI component scoring service.

This module supplies the AI component score used by Investment Score V2.
It deliberately does not generate the final BUY/HOLD/SELL recommendation.
The final recommendation belongs exclusively to recommendation_service.
"""

import math


def _number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def get_ai_recommendation(stock_data, history=None):
    """Return the AI component score and supporting reasons."""
    data = stock_data if isinstance(stock_data, dict) else {}
    score = 50.0
    reasons = []

    pe = _number(data.get("pe"))
    if pe is not None:
        if 0 < pe <= 20:
            score += 10
            reasons.append("Attractive PE Ratio")
        elif pe <= 30:
            score += 5
            reasons.append("Reasonable PE Ratio")
        elif pe > 30:
            score -= 5
            reasons.append("High PE Ratio")

    eps = _number(data.get("eps"))
    if eps is not None:
        if eps > 0:
            score += 10
            reasons.append("Positive Earnings")
        else:
            score -= 15
            reasons.append("Negative Earnings")

    margin = _number(data.get("profit_margin"))
    if margin is not None:
        if margin > 0.15:
            score += 10
            reasons.append("Excellent Profit Margin")
        elif margin > 0.05:
            score += 5
            reasons.append("Healthy Profit Margin")
        else:
            score -= 5
            reasons.append("Weak Profit Margin")

    roe = _number(data.get("roe"))
    if roe is not None:
        if roe > 0.15:
            score += 10
            reasons.append("Strong ROE")
        elif roe > 0.08:
            score += 5
            reasons.append("Good ROE")

    beta = _number(data.get("beta"))
    if beta is not None:
        if beta < 1:
            score += 5
            reasons.append("Lower Market Risk")
        elif beta > 1.5:
            score -= 5
            reasons.append("High Volatility")

    if history is not None and not getattr(history, "empty", True):
        if "EMA200" in history.columns and "Close" in history.columns:
            close = _number(history["Close"].iloc[-1])
            ema200 = _number(history["EMA200"].iloc[-1])
            if close is not None and ema200 is not None:
                if close > ema200:
                    score += 15
                    reasons.append("Price Above EMA200")
                else:
                    score -= 10
                    reasons.append("Price Below EMA200")

    score = round(max(0.0, min(score, 100.0)))

    return {
        "score": score,
        "reasons": reasons,
        "component": "AI",
    }
