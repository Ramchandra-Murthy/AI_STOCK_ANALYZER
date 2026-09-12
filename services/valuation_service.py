def _safe_float(value, default=None):
    """Safely convert a value to float."""
    try:
        if value is None:
            return default

        value = float(value)

        if value != value:  # NaN
            return default

        return value

    except (TypeError, ValueError):
        return default


def generate_valuation_analysis(
    data,
    fundamental_score,
    investment_score,
):
    """
    Fundamental Valuation Engine V3.

    Produces an earnings-based fair-value estimate using:
    - Current price
    - EPS
    - Trailing P/E
    - Forward P/E
    - Growth
    - Fundamental quality

    This engine is independent of the technical trade target.
    """

    data = data if isinstance(data, dict) else {}

    current_price = _safe_float(data.get("price"))
    eps = _safe_float(data.get("eps"))
    trailing_pe = _safe_float(data.get("pe"))
    forward_pe = _safe_float(data.get("forward_pe"))

    revenue_growth = _safe_float(data.get("revenue_growth"))

    earnings_growth = _safe_float(data.get("earnings_growth"))

    fundamental_score = _safe_float(fundamental_score, 0) or 0

    investment_score = _safe_float(investment_score, 0) or 0

    # ======================================================
    # VALIDATION
    # ======================================================

    if current_price is None or current_price <= 0 or eps is None or eps <= 0:
        return {
            "status": "UNAVAILABLE",
            "message": ("Insufficient price or earnings data " "for earnings-based valuation."),
        }

    # ======================================================
    # BASE FAIR P/E
    # ======================================================

    pe_candidates = []

    if trailing_pe is not None and trailing_pe > 0:
        pe_candidates.append(trailing_pe)

    if forward_pe is not None and forward_pe > 0:
        pe_candidates.append(forward_pe)

    if pe_candidates:
        base_pe = sum(pe_candidates) / len(pe_candidates)
    else:
        base_pe = 18.0

    # Prevent extreme multiples from dominating valuation.
    base_pe = max(8.0, min(base_pe, 35.0))

    # ======================================================
    # FUNDAMENTAL QUALITY ADJUSTMENT
    # ======================================================

    if fundamental_score >= 80:
        quality_adjustment = 1.10

    elif fundamental_score >= 70:
        quality_adjustment = 1.05

    elif fundamental_score >= 60:
        quality_adjustment = 1.00

    elif fundamental_score >= 50:
        quality_adjustment = 0.95

    else:
        quality_adjustment = 0.90

    # ======================================================
    # GROWTH ADJUSTMENT
    # ======================================================

    growth_adjustment = 1.00

    if earnings_growth is not None:

        if earnings_growth >= 0.20:
            growth_adjustment += 0.10

        elif earnings_growth >= 0.10:
            growth_adjustment += 0.05

        elif earnings_growth < 0:
            growth_adjustment -= 0.10

    if revenue_growth is not None:

        if revenue_growth >= 0.20:
            growth_adjustment += 0.05

        elif revenue_growth >= 0.10:
            growth_adjustment += 0.025

        elif revenue_growth < 0:
            growth_adjustment -= 0.05

    growth_adjustment = max(
        0.80,
        min(growth_adjustment, 1.20),
    )

    # ======================================================
    # FAIR P/E
    # ======================================================

    fair_pe = base_pe * quality_adjustment * growth_adjustment

    fair_pe = max(
        8.0,
        min(fair_pe, 35.0),
    )

    # ======================================================
    # FAIR VALUE
    # ======================================================

    fair_value = eps * fair_pe

    upside_percent = ((fair_value - current_price) / current_price) * 100

    # Margin of safety from investor's perspective.
    margin_of_safety = ((fair_value - current_price) / fair_value) * 100

    # ======================================================
    # VALUATION STATUS
    # ======================================================

    if upside_percent >= 20:
        valuation_status = "UNDERVALUED"

    elif upside_percent >= 5:
        valuation_status = "SLIGHTLY UNDERVALUED"

    elif upside_percent > -5:
        valuation_status = "FAIRLY VALUED"

    elif upside_percent > -20:
        valuation_status = "SLIGHTLY OVERVALUED"

    else:
        valuation_status = "OVERVALUED"

    # ======================================================
    # VALUATION CONVICTION
    # ======================================================

    if fundamental_score >= 75 and upside_percent >= 15:
        valuation_conviction = "HIGH"

    elif fundamental_score >= 60 and upside_percent >= 5:
        valuation_conviction = "MODERATE"

    elif abs(upside_percent) < 5:
        valuation_conviction = "NEUTRAL"

    else:
        valuation_conviction = "LOW"

    # ======================================================
    # VALUATION RANGE
    # ======================================================

    bear_pe = fair_pe * 0.85
    bull_pe = fair_pe * 1.15

    bear_value = eps * bear_pe
    bull_value = eps * bull_pe

    # ======================================================
    # EXPLANATION
    # ======================================================

    reasons = []

    reasons.append(f"EPS used for valuation: " f"{eps:.2f}.")

    reasons.append(f"Base P/E reference: " f"{base_pe:.2f}x.")

    reasons.append(f"Quality-adjusted and growth-adjusted " f"fair P/E: {fair_pe:.2f}x.")

    if earnings_growth is not None:
        reasons.append(f"Earnings growth: " f"{earnings_growth * 100:.2f}%.")

    if revenue_growth is not None:
        reasons.append(f"Revenue growth: " f"{revenue_growth * 100:.2f}%.")

    reasons.append(f"Fundamental score: " f"{fundamental_score:.0f}/100.")

    # ======================================================
    # RETURN RESULT
    # ======================================================

    return {
        "status": "OK",
        "current_price": round(current_price, 2),
        "eps": round(eps, 2),
        "trailing_pe": (round(trailing_pe, 2) if trailing_pe is not None else None),
        "forward_pe": (round(forward_pe, 2) if forward_pe is not None else None),
        "base_pe": round(base_pe, 2),
        "fair_pe": round(fair_pe, 2),
        "fair_value": round(fair_value, 2),
        "bear_value": round(bear_value, 2),
        "bull_value": round(bull_value, 2),
        "upside_percent": round(upside_percent, 2),
        "margin_of_safety": round(margin_of_safety, 2),
        "valuation_status": valuation_status,
        "valuation_conviction": (valuation_conviction),
        "fundamental_score": round(fundamental_score),
        "investment_score": round(investment_score),
        "reasons": reasons,
    }
