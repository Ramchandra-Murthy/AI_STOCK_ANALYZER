def _safe_float(value, default=None):
    """Safely convert a value to float."""
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_reasons(reasons):
    """Return a clean list of non-empty reason strings."""
    if not isinstance(reasons, (list, tuple)):
        return []

    return [
        str(reason).strip()
        for reason in reasons
        if reason is not None and str(reason).strip()
    ]


def generate_investment_thesis(
    data,
    investment_score,
    technical_score,
    fundamental_score,
    ai_result,
    score_breakdown,
    technical_reasons,
    fundamental_reasons,
    trade_plan=None,
):
    """
    Generate a structured investment thesis using the existing
    analytical outputs of AI Stock Analyzer Pro.

    This engine does not replace the existing scoring engines.
    It interprets their outputs into an analyst-style research thesis.
    """

    data = data if isinstance(data, dict) else {}
    ai_result = ai_result if isinstance(ai_result, dict) else {}
    score_breakdown = score_breakdown if isinstance(score_breakdown, dict) else {}
    trade_plan = trade_plan if isinstance(trade_plan, dict) else {}

    technical_reasons = _clean_reasons(technical_reasons)
    fundamental_reasons = _clean_reasons(fundamental_reasons)
    _clean_reasons(ai_result.get("reasons", []))

    investment_score = _safe_float(investment_score)
    technical_score = _safe_float(technical_score)
    fundamental_score = _safe_float(fundamental_score)
    ai_score = _safe_float(ai_result.get("score"))

    # Never manufacture a thesis from missing upstream evidence.
    if investment_score is None:
        return {
            "company": data.get("company", "The company"),
            "sector": data.get("sector", "N/A"),
            "industry": data.get("industry", "N/A"),
            "investment_score": None,
            "conviction": "UNAVAILABLE",
            "thesis": "Investment thesis unavailable because the Investment Score was not produced.",
            "strengths": [],
            "concerns": ["Upstream scoring data is unavailable."],
            "catalysts": [],
            "bull_case": None,
            "base_case": None,
            "bear_case": None,
            "current_price": None,
            "target_price": None,
            "stop_loss": None,
        }

    # Missing component scores are evidence gaps, not neutral 50s.
    # The Investment Score has already validated core evidence; preserve that
    # contract here instead of manufacturing inputs for the thesis.
    if technical_score is None or fundamental_score is None:
        return {
            "status": "INSUFFICIENT DATA",
            "message": "Technical and Fundamental evidence are required for a reliable investment thesis.",
            "investment_score": investment_score,
            "technical_score": technical_score,
            "fundamental_score": fundamental_score,
            "ai_score": ai_score,
            "current_price": None,
            "target_price": None,
            "recommendation": "INSUFFICIENT DATA",
            "confidence": 0,
        }

    if ai_score is None:
        ai_score = None

    stability_score = (
        _safe_float(
            score_breakdown.get("Stability"),
            0,
        )
        or 0
    )

    company = data.get("company", "The company")
    sector = data.get("sector", "N/A")
    industry = data.get("industry", "N/A")

    # ==========================================================
    # OVERALL THESIS
    # ==========================================================

    if investment_score >= 80:
        thesis = (
            f"{company} currently presents a strong investment profile. "
            "The combined fundamental, technical, AI and stability signals "
            "indicate favorable overall investment quality."
        )

    elif investment_score >= 65:
        thesis = (
            f"{company} currently presents a moderately attractive "
            "investment profile. Several analytical factors are supportive, "
            "although investors should continue to evaluate valuation, "
            "technical conditions and company-specific risks."
        )

    elif investment_score >= 50:
        thesis = (
            f"{company} currently presents a mixed investment profile. "
            "Fundamental or stability characteristics may provide support, "
            "but weaker components reduce overall conviction."
        )

    elif investment_score >= 35:
        thesis = (
            f"{company} currently presents a cautious investment profile. "
            "The analytical framework identifies material weaknesses that "
            "should be considered before taking a new position."
        )

    else:
        thesis = (
            f"{company} currently presents a weak investment profile under "
            "the existing analytical framework, with limited support from "
            "the combined scoring components."
        )

    # ==========================================================
    # STRENGTHS
    # ==========================================================

    strengths = []

    if fundamental_score >= 70:
        strengths.append(
            f"Fundamental score is strong at " f"{fundamental_score:.0f}/100."
        )

    if technical_score >= 70:
        strengths.append(f"Technical score is strong at " f"{technical_score:.0f}/100.")

    if ai_score >= 70:
        strengths.append(f"AI model score is supportive at " f"{ai_score:.0f}/100.")

    if stability_score >= 70:
        strengths.append(f"Stability score is strong at " f"{stability_score:.0f}/100.")

    revenue_growth = _safe_float(data.get("revenue_growth"))

    if revenue_growth is not None and revenue_growth > 0.10:
        strengths.append(
            f"Revenue growth is positive at " f"{revenue_growth * 100:.2f}%."
        )

    operating_cash_flow = _safe_float(data.get("operating_cash_flow"))

    if operating_cash_flow is not None and operating_cash_flow > 0:
        strengths.append("Operating cash flow is positive.")

    free_cash_flow = _safe_float(data.get("free_cash_flow"))

    if free_cash_flow is not None and free_cash_flow > 0:
        strengths.append("Free cash flow is positive.")

    # Add selected existing fundamental reasons.
    for reason in fundamental_reasons:
        lower_reason = reason.lower()

        positive_terms = [
            "reasonable",
            "strong",
            "positive",
            "manageable",
            "adequate",
            "covers",
        ]

        if any(term in lower_reason for term in positive_terms):
            if reason not in strengths:
                strengths.append(reason)

    # ==========================================================
    # CONCERNS
    # ==========================================================

    concerns = []

    if technical_score < 50:
        concerns.append(f"Technical score is weak at " f"{technical_score:.0f}/100.")

    if fundamental_score < 50:
        concerns.append(
            f"Fundamental score is weak at " f"{fundamental_score:.0f}/100."
        )

    if ai_score < 50:
        concerns.append(f"AI model score is weak at " f"{ai_score:.0f}/100.")

    earnings_growth = _safe_float(data.get("earnings_growth"))

    if earnings_growth is not None and earnings_growth < 0:
        concerns.append(
            f"Earnings growth is negative at " f"{earnings_growth * 100:.2f}%."
        )

    for reason in technical_reasons:
        lower_reason = reason.lower()

        negative_terms = [
            "weak",
            "bearish",
            "below",
            "negative",
            "resistance",
        ]

        if any(term in lower_reason for term in negative_terms):
            if reason not in concerns:
                concerns.append(reason)

    # ==========================================================
    # CATALYSTS
    # ==========================================================

    catalysts = []

    if revenue_growth is not None and revenue_growth > 0.15:
        catalysts.append(
            "Continued strong revenue growth could improve "
            "future earnings performance."
        )

    if earnings_growth is not None and earnings_growth < 0:
        catalysts.append(
            "A recovery in earnings growth could materially improve "
            "the investment outlook."
        )

    if technical_score < 50:
        catalysts.append(
            "Improvement in technical momentum and trend confirmation "
            "could strengthen the investment setup."
        )

    if fundamental_score >= 70:
        catalysts.append(
            "Sustained fundamental performance could support " "longer-term valuation."
        )

    # ==========================================================
    # SCENARIOS
    # ==========================================================

    current_price = _safe_float(trade_plan.get("current_price"))

    target_price = _safe_float(trade_plan.get("target_price"))

    stop_loss = _safe_float(trade_plan.get("stop_loss"))

    if target_price is not None:
        bull_case = (
            f"Improving technical momentum combined with sustained "
            f"fundamental performance could support movement toward "
            f"the current model target of ₹{target_price:,.2f}."
        )
    else:
        bull_case = (
            "Improving earnings, stronger technical momentum and "
            "continued fundamental strength could produce a more "
            "favorable investment outcome."
        )

    base_case = (
        f"The base case assumes that {company} continues to reflect "
        f"its current mixed analytical profile, with an Investment "
        f"Score of {investment_score:.0f}/100, Fundamental Score of "
        f"{fundamental_score:.0f}/100 and Technical Score of "
        f"{technical_score:.0f}/100."
    )

    if stop_loss is not None:
        bear_case = (
            f"Further deterioration in technical conditions or "
            f"fundamental performance could increase downside risk. "
            f"The current rule-based trade plan identifies "
            f"₹{stop_loss:,.2f} as the stop-loss reference level."
        )
    else:
        bear_case = (
            "Weakening fundamentals, deteriorating earnings or "
            "continued bearish technical conditions could result "
            "in downside risk."
        )

    # ==========================================================
    # CONVICTION
    # ==========================================================

    if investment_score >= 80:
        conviction = "HIGH"
    elif investment_score >= 65:
        conviction = "MODERATE-HIGH"
    elif investment_score >= 50:
        conviction = "MODERATE"
    elif investment_score >= 35:
        conviction = "LOW"
    else:
        conviction = "VERY LOW"

    # ==========================================================
    # RETURN RESULT
    # ==========================================================

    return {
        "company": company,
        "sector": sector,
        "industry": industry,
        "investment_score": round(investment_score),
        "conviction": conviction,
        "thesis": thesis,
        "strengths": strengths[:8],
        "concerns": concerns[:8],
        "catalysts": catalysts[:6],
        "bull_case": bull_case,
        "base_case": base_case,
        "bear_case": bear_case,
        "current_price": current_price,
        "target_price": target_price,
        "stop_loss": stop_loss,
    }
