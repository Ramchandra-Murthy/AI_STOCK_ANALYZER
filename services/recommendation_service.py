# ==========================================================
# RECOMMENDATION SERVICE
# ==========================================================

import math


def generate_recommendation(investment_score):
    """Generate a bounded recommendation from the authoritative score."""
    try:
        overall_score = float(investment_score)
    except (TypeError, ValueError):
        overall_score = 0.0

    if not math.isfinite(overall_score):
        overall_score = 0.0
    overall_score = max(0.0, min(overall_score, 100.0))

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
