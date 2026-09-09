import math


def _safe_float(value, default=None):
    """Safely convert a value to a finite float."""
    try:
        if value is None:
            return default
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def generate_scenario_analysis(
    data,
    investment_score,
    technical_score,
    fundamental_score,
    ai_result,
    score_breakdown,
    trade_plan,
):
    """Generate scenarios without replacing unavailable evidence with neutral values."""

    data = data if isinstance(data, dict) else {}
    ai_result = ai_result if isinstance(ai_result, dict) else {}
    score_breakdown = score_breakdown if isinstance(score_breakdown, dict) else {}
    trade_plan = trade_plan if isinstance(trade_plan, dict) else {}

    investment_score = _safe_float(investment_score)
    technical_score = _safe_float(technical_score)
    fundamental_score = _safe_float(fundamental_score)
    ai_score = _safe_float(ai_result.get("score"))
    stability_score = _safe_float(score_breakdown.get("Stability"))

    if investment_score is None:
        return {
            "status": "UNAVAILABLE",
            "message": "Scenario analysis unavailable because the Investment Score was not produced.",
            "bull_case": None,
            "base_case": None,
            "bear_case": None,
            "reward_risk": None,
        }

    # Investment Score V2 requires Technical and Fundamental core evidence.
    # Preserve the same contract here instead of manufacturing neutral 50s.
    if technical_score is None or fundamental_score is None:
        return {
            "status": "INSUFFICIENT DATA",
            "message": "Technical and Fundamental evidence are required for scenario analysis.",
            "investment_score": investment_score,
            "technical_score": technical_score,
            "fundamental_score": fundamental_score,
            "ai_score": ai_score,
            "stability_score": stability_score,
            "bull": None,
            "base": None,
            "bear": None,
            "reward_risk": None,
        }

    current_price = _safe_float(trade_plan.get("current_price"))
    target_price = _safe_float(trade_plan.get("target_price"))
    stop_loss = _safe_float(trade_plan.get("stop_loss"))

    bull_return = None
    bear_return = None

    if current_price is not None and current_price > 0 and target_price is not None:
        value = ((target_price - current_price) / current_price) * 100
        bull_return = value if math.isfinite(value) else None

    if current_price is not None and current_price > 0 and stop_loss is not None:
        value = ((stop_loss - current_price) / current_price) * 100
        bear_return = value if math.isfinite(value) else None

    upside_amount = None
    downside_amount = None
    reward_risk = None

    if current_price is not None and target_price is not None:
        upside_amount = max(target_price - current_price, 0)

    if current_price is not None and stop_loss is not None:
        downside_amount = max(current_price - stop_loss, 0)

    if upside_amount is not None and downside_amount is not None and downside_amount > 0:
        value = upside_amount / downside_amount
        reward_risk = value if math.isfinite(value) else None

    # Stability is optional evidence. Do not turn missing stability into a
    # genuine zero score or imply weak stability when the metric is absent.
    if stability_score is None:
        long_term_view = "UNAVAILABLE"
    elif fundamental_score >= 75 and stability_score >= 70:
        long_term_view = "STRONG"
    elif fundamental_score >= 65 and stability_score >= 60:
        long_term_view = "MODERATELY CONSTRUCTIVE"
    elif fundamental_score >= 50:
        long_term_view = "NEUTRAL"
    else:
        long_term_view = "CAUTIOUS"

    if technical_score >= 75:
        entry_quality = "STRONG"
    elif technical_score >= 60:
        entry_quality = "FAVORABLE"
    elif technical_score >= 45:
        entry_quality = "NEUTRAL"
    else:
        entry_quality = "WEAK"

    if reward_risk is not None and reward_risk < 1:
        entry_quality = "WEAK"

    if (
        investment_score >= 75
        and technical_score >= 60
        and (reward_risk is None or reward_risk >= 1.5)
    ):
        action = "BUY"
    elif investment_score >= 55 and fundamental_score >= 60:
        if technical_score < 50:
            action = "HOLD / WAIT FOR TECHNICAL CONFIRMATION"
        elif reward_risk is not None and reward_risk < 1:
            action = "HOLD / WAIT FOR BETTER ENTRY"
        else:
            action = "HOLD"
    else:
        action = "AVOID / REVIEW"

    bull_assumptions = [
        "Technical momentum improves.",
        "Fundamental performance remains supportive.",
        "Price moves toward the current model target.",
    ]

    base_assumptions = [
        "Current fundamental conditions remain broadly stable.",
        "No major change occurs in technical trend.",
        "The stock remains near its current analytical profile.",
    ]

    bear_assumptions = [
        "Technical weakness persists or deteriorates.",
        "Earnings or fundamental conditions weaken.",
        "Price moves toward the current risk-control level.",
    ]

    return {
        "status": "OK",
        "current_price": current_price,
        "bull": {
            "price": target_price,
            "return_percent": round(bull_return, 2) if bull_return is not None else None,
            "assumptions": bull_assumptions,
        },
        "base": {
            "price": current_price,
            "return_percent": 0.0 if current_price is not None else None,
            "assumptions": base_assumptions,
        },
        "bear": {
            "price": stop_loss,
            "return_percent": round(bear_return, 2) if bear_return is not None else None,
            "assumptions": bear_assumptions,
        },
        "reward_risk": round(reward_risk, 2) if reward_risk is not None else None,
        "long_term_view": long_term_view,
        "entry_quality": entry_quality,
        "action": action,
        "investment_score": round(investment_score),
        "technical_score": round(technical_score),
        "fundamental_score": round(fundamental_score),
        "ai_score": round(ai_score) if ai_score is not None else None,
        "stability_score": round(stability_score) if stability_score is not None else None,
    }
