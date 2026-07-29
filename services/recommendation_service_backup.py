def generate_recommendation(
    technical_score,
    fundamental_score,
    news_score=70,
    valuation_score=70,
):
    """
    Generate an overall investment recommendation.
    """

    overall = (
        technical_score * 0.35
        + fundamental_score * 0.35
        + news_score * 0.15
        + valuation_score * 0.15
    )

    if overall >= 85:
        recommendation = "🟢 STRONG BUY"

    elif overall >= 70:
        recommendation = "🟢 BUY"

    elif overall >= 55:
        recommendation = "🟡 HOLD"

    elif overall >= 40:
        recommendation = "🟠 SELL"

    else:
        recommendation = "🔴 STRONG SELL"

    confidence = round(overall)

    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "overall_score": round(overall, 2),
    }
