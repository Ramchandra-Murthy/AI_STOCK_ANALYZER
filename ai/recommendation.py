def get_ai_recommendation(data, history=None):
    """
    AI Recommendation Engine
    """

    score = 50
    reasons = []

    # PE Ratio
    pe = data.get("pe")
    if isinstance(pe, (int, float)):
        if pe < 20:
            score += 10
            reasons.append("PE ratio is attractive.")
        elif pe < 30:
            score += 5
            reasons.append("PE ratio is reasonable.")
        else:
            score -= 5
            reasons.append("PE ratio is relatively high.")

    # EPS
    eps = data.get("eps")
    if isinstance(eps, (int, float)):
        if eps > 0:
            score += 10
            reasons.append("Positive earnings per share.")
        else:
            score -= 15
            reasons.append("Negative earnings per share.")

    # Profit Margin
    margin = data.get("profit_margin")
    if isinstance(margin, (int, float)):
        if margin > 0.15:
            score += 10
            reasons.append("Strong profit margin.")
        elif margin > 0.05:
            score += 5
            reasons.append("Healthy profit margin.")
        else:
            score -= 5
            reasons.append("Weak profit margin.")

    # Beta
    beta = data.get("beta")
    if isinstance(beta, (int, float)):
        if beta < 1:
            score += 5
            reasons.append("Low market volatility.")
        elif beta > 1.5:
            score -= 5
            reasons.append("High market volatility.")

    # EMA200 Trend
    if history is not None and not history.empty:
        if "EMA200" in history.columns:
            close = history["Close"].iloc[-1]
            ema200 = history["EMA200"].iloc[-1]

            if close > ema200:
                score += 15
                reasons.append("Price is above EMA200.")
            else:
                score -= 10
                reasons.append("Price is below EMA200.")

    score = max(0, min(score, 100))

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