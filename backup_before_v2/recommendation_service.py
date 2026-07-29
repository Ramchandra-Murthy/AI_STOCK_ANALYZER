def generate_recommendation(
    investment_score,
):
    """
    Generate the final investment recommendation
    from the authoritative Investment Score.

    Score bands:
        85-100  STRONG BUY
        70-84   BUY
        55-69   HOLD
        40-54   SELL
        0-39    STRONG SELL
    """

    try:
        overall = float(investment_score)

    except (TypeError, ValueError):
        overall = 50.0

    overall = max(
        0.0,
        min(overall, 100.0),
    )

    if overall >= 85:
        recommendation = "STRONG BUY"

    elif overall >= 70:
        recommendation = "BUY"

    elif overall >= 55:
        recommendation = "HOLD"

    elif overall >= 40:
        recommendation = "SELL"

    else:
        recommendation = "STRONG SELL"

    return {
        "recommendation": recommendation,
        "confidence": round(overall),
        "overall_score": round(overall, 2),
    }
