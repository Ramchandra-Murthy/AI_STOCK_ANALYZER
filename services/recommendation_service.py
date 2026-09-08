# ==========================================================
# RECOMMENDATION SERVICE
# ==========================================================


def generate_recommendation(investment_score):
    """
    Generate the final investment recommendation from
    the authoritative Investment Score.

    Score Bands
    -----------
    85 - 100 : STRONG BUY
    70 - 84  : BUY
    55 - 69  : HOLD
    40 - 54  : SELL
    0  - 39  : STRONG SELL
    """

    # ------------------------------------------------------
    # Validate score
    # ------------------------------------------------------

    # Missing evidence is not a HOLD signal.
    if investment_score is None:
        return {
            "recommendation": "INSUFFICIENT DATA",
            "confidence": 0,
            "overall_score": None,
        }

    try:
        overall_score = float(investment_score)

    except (TypeError, ValueError):
        return {
            "recommendation": "INSUFFICIENT DATA",
            "confidence": 0,
            "overall_score": None,
        }

    # Keep score inside 0-100
    overall_score = max(
        0.0,
        min(overall_score, 100.0),
    )

    # ------------------------------------------------------
    # Recommendation
    # ------------------------------------------------------

    if overall_score >= 85:
        recommendation = "STRONG BUY"

    elif overall_score >= 70:
        recommendation = "BUY"

    elif overall_score >= 55:
        recommendation = "HOLD"

    elif overall_score >= 40:
        recommendation = "SELL"

    else:
        recommendation = "STRONG SELL"

    # ------------------------------------------------------
    # Confidence
    # ------------------------------------------------------

    confidence = round(overall_score)

    # ------------------------------------------------------
    # Return result
    # ------------------------------------------------------

    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "overall_score": round(overall_score, 2),
    }
