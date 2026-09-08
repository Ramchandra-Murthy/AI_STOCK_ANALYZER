import math

# ==========================================================
# HELPERS
# ==========================================================


def _safe_float(value):
    """
    Convert a value to a finite float.

    Returns None if the value cannot be converted.
    """

    try:
        value = float(value)

        if not math.isfinite(value):
            return None

        return value

    except (TypeError, ValueError):
        return None


def _clamp(value, minimum=0.0, maximum=100.0):
    """
    Clamp a numeric value between minimum and maximum.
    """

    return max(
        minimum,
        min(float(value), maximum),
    )


# ==========================================================
# STABILITY / RISK SCORE
# ==========================================================


def calculate_stability_score(data):
    """
    Calculate a 0-100 stability score.

    Uses:
        Beta             40%
        Debt / Equity    30%
        Current Ratio    30%

    Missing metrics are availability-normalized so that
    unavailable data does not automatically receive zero.
    """

    if not isinstance(data, dict):
        return 50.0, ["Stability data unavailable."]

    components = []
    reasons = []

    # ------------------------------------------------------
    # Beta — 40 points
    # ------------------------------------------------------

    beta = _safe_float(data.get("beta"))

    if beta is not None:

        if beta < 0:
            beta_points = 20

            reasons.append(f"Beta of {beta:.2f} requires cautious interpretation.")

        elif beta <= 0.75:
            beta_points = 40

            reasons.append(
                f"Beta of {beta:.2f} indicates relatively low market volatility."
            )

        elif beta <= 1.00:
            beta_points = 35

            reasons.append(f"Beta of {beta:.2f} indicates below-market volatility.")

        elif beta <= 1.25:
            beta_points = 28

            reasons.append(f"Beta of {beta:.2f} indicates moderate market volatility.")

        elif beta <= 1.50:
            beta_points = 20

            reasons.append(f"Beta of {beta:.2f} indicates elevated volatility.")

        elif beta <= 2.00:
            beta_points = 10

            reasons.append(f"Beta of {beta:.2f} indicates high market volatility.")

        else:
            beta_points = 0

            reasons.append(f"Beta of {beta:.2f} indicates very high market volatility.")

        components.append((beta_points, 40))

    # ------------------------------------------------------
    # Debt / Equity — 30 points
    #
    # Yahoo debtToEquity is percentage-style:
    #     36.653 -> 0.36653x
    # ------------------------------------------------------

    debt_to_equity_raw = _safe_float(data.get("debt_to_equity"))

    if debt_to_equity_raw is not None:

        debt_to_equity = debt_to_equity_raw / 100.0

        if debt_to_equity <= 0.30:
            debt_points = 30

            reasons.append(
                f"Debt-to-equity of {debt_to_equity:.2f}x indicates low leverage."
            )

        elif debt_to_equity <= 0.75:
            debt_points = 26

            reasons.append(
                f"Debt-to-equity of {debt_to_equity:.2f}x indicates manageable leverage."
            )

        elif debt_to_equity <= 1.50:
            debt_points = 18

            reasons.append(
                f"Debt-to-equity of {debt_to_equity:.2f}x indicates moderate leverage."
            )

        elif debt_to_equity <= 2.00:
            debt_points = 10

            reasons.append(
                f"Debt-to-equity of {debt_to_equity:.2f}x indicates elevated leverage."
            )

        else:
            debt_points = 0

            reasons.append(
                f"Debt-to-equity of {debt_to_equity:.2f}x indicates high leverage."
            )

        components.append((debt_points, 30))

    # ------------------------------------------------------
    # Current Ratio — 30 points
    # ------------------------------------------------------

    current_ratio = _safe_float(data.get("current_ratio"))

    if current_ratio is not None:

        if 1.50 <= current_ratio <= 3.00:
            liquidity_points = 30

            reasons.append(
                f"Current ratio of {current_ratio:.2f}x indicates healthy liquidity."
            )

        elif 1.00 <= current_ratio < 1.50:
            liquidity_points = 24

            reasons.append(
                f"Current ratio of {current_ratio:.2f}x indicates adequate liquidity."
            )

        elif current_ratio > 3.00:
            liquidity_points = 24

            reasons.append(
                f"Current ratio of {current_ratio:.2f}x indicates strong liquidity."
            )

        elif current_ratio >= 0.75:
            liquidity_points = 12

            reasons.append(
                f"Current ratio of {current_ratio:.2f}x indicates tight liquidity."
            )

        else:
            liquidity_points = 0

            reasons.append(
                f"Current ratio of {current_ratio:.2f}x indicates weak liquidity."
            )

        components.append((liquidity_points, 30))

    # ------------------------------------------------------
    # Normalize available components to 100
    # ------------------------------------------------------

    if not components:
        return 50.0, ["Insufficient data to calculate stability score."]

    earned = sum(item[0] for item in components)

    possible = sum(item[1] for item in components)

    stability_score = (earned / possible) * 100.0

    stability_score = round(
        _clamp(stability_score),
        2,
    )

    return stability_score, reasons


# ==========================================================
# INVESTMENT SCORE V2
# ==========================================================


def calculate_investment_score(
    technical_score,
    fundamental_score,
    ai_result=None,
    data=None,
):
    """Calculate an evidence-aware Investment Score V2.

    Missing components are excluded and their weights are renormalized.
    A score is never manufactured from a neutral 50.0 fallback.
    """
    candidates = [
        ("Technical", _safe_float(technical_score), 0.35),
        ("Fundamental", _safe_float(fundamental_score), 0.40),
    ]

    ai_score = None
    if isinstance(ai_result, dict):
        ai_score = _safe_float(ai_result.get("score"))
    candidates.append(("AI", ai_score, 0.15))

    stability_score, stability_reasons = calculate_stability_score(
        data if isinstance(data, dict) else {}
    )
    stability_available = isinstance(data, dict) and bool(
        any(data.get(k) is not None for k in ("beta", "debt_to_equity", "current_ratio"))
    )
    candidates.append(
        ("Stability", stability_score if stability_available else None, 0.10)
    )

    available = [
        (name, _clamp(value), weight)
        for name, value, weight in candidates
        if value is not None
    ]

    if not available:
        return 0, {
            "status": "UNAVAILABLE",
            "message": "Insufficient evidence to calculate Investment Score.",
            "available_components": [],
            "missing_components": [name for name, _, _ in candidates],
            "Stability Reasons": stability_reasons,
        }

    total_weight = sum(weight for _, _, weight in available)
    overall = round(
        _clamp(sum(value * weight for _, value, weight in available) / total_weight)
    )

    breakdown = {
        "status": "OK",
        "available_components": [name for name, _, _ in available],
        "missing_components": [name for name, _, _ in candidates if name not in {x[0] for x in available}],
        "weight_normalization": round(total_weight, 4),
        "Technical": None,
        "Fundamental": None,
        "AI": None,
        "Stability": None,
        "Technical Contribution": 0.0,
        "Fundamental Contribution": 0.0,
        "AI Contribution": 0.0,
        "Stability Contribution": 0.0,
        "Stability Reasons": stability_reasons,
    }

    for name, value, weight in available:
        breakdown[name] = round(value, 2)
        breakdown[f"{name} Contribution"] = round((value * weight) / total_weight, 2)

    return overall, breakdown
