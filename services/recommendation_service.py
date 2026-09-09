# ==========================================================
# RECOMMENDATION SERVICE
# ==========================================================

import math


def generate_recommendation(investment_score):
    """
    Generate the final investment recommendation from
    the authoritative Investment Score.

    Missing, non-finite, non-numeric, or out-of-domain scores
    are not converted into a recommendation.
    """

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

    if not math.isfinite(overall_score) or not 0.0 <= overall_score <= 100.0:
        return {
            "recommendation": "INSUFFICIENT DATA",
            "confidence": 0,
            "overall_score": None,
        }

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

    return {
        "recommendation": recommendation,
        "confidence": round(overall_score),
        "overall_score": round(overall_score, 2),
    }
