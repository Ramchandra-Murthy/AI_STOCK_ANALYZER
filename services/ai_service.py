"""
AI Recommendation Service
AI Stock Analyzer Pro
Version 3.6
"""


def get_ai_recommendation(stock_data, history=None):
    """
    Generate a rule-based AI recommendation.

    Parameters
    ----------
    stock_data : dict
        Dictionary returned by research_service.

    history : pandas.DataFrame, optional
        Historical OHLC data with EMA200.

    Returns
    -------
    dict
    """

    score = 50
    reasons = []

    # -----------------------------
    # PE Ratio
    # -----------------------------
    pe = stock_data.get("pe")

    if isinstance(pe, (int, float)):
        if pe <= 20:
            score += 10
            reasons.append("Attractive PE Ratio")
        elif pe <= 30:
            score += 5
            reasons.append("Reasonable PE Ratio")
        else:
            score -= 5
            reasons.append("High PE Ratio")

    # -----------------------------
    # EPS
    # -----------------------------
    eps = stock_data.get("eps")

    if isinstance(eps, (int, float)):
        if eps > 0:
            score += 10
            reasons.append("Positive Earnings")
        else:
            score -= 15
            reasons.append("Negative Earnings")

    # -----------------------------
    # Profit Margin
    # -----------------------------
    margin = stock_data.get("profit_margin")

    if isinstance(margin, (int, float)):
        if margin > 0.15:
            score += 10
            reasons.append("Excellent Profit Margin")
        elif margin > 0.05:
            score += 5
            reasons.append("Healthy Profit Margin")
        else:
            score -= 5
            reasons.append("Weak Profit Margin")

    # -----------------------------
    # ROE
    # -----------------------------
    roe = stock_data.get("roe")

    if isinstance(roe, (int, float)):
        if roe > 0.15:
            score += 10
            reasons.append("Strong ROE")
        elif roe > 0.08:
            score += 5
            reasons.append("Good ROE")

    # -----------------------------
    # Beta
    # -----------------------------
    beta = stock_data.get("beta")

    if isinstance(beta, (int, float)):
        if beta < 1:
            score += 5
            reasons.append("Lower Market Risk")
        elif beta > 1.5:
            score -= 5
            reasons.append("High Volatility")

    # -----------------------------
    # EMA200 Trend
    # -----------------------------
    if history is not None:

        if (
            not history.empty
            and "EMA200" in history.columns
            and "Close" in history.columns
        ):

            close = history["Close"].iloc[-1]
            ema200 = history["EMA200"].iloc[-1]

            if close > ema200:
                score += 15
                reasons.append("Price Above EMA200")
            else:
                score -= 10
                reasons.append("Price Below EMA200")

    # -----------------------------
    # Clamp
    # -----------------------------
    score = max(0, min(score, 100))

    # -----------------------------
    # Recommendation
    # -----------------------------
    if score >= 80:
        recommendation = "BUY"
        risk = "Low"

    elif score >= 60:
        recommendation = "HOLD"
        risk = "Medium"

    else:
        recommendation = "SELL"
        risk = "High"

    return {
        "score": score,
        "recommendation": recommendation,
        "risk": risk,
        "reasons": reasons,
    }