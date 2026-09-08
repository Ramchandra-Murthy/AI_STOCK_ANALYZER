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
        return None, ["Stability data unavailable."]

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
        return None, ["Insufficient data to calculate stability score."]

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
    """
    Calculate the Investment Score using only available evidence.

    Missing evidence is not converted into a neutral 50 or a punitive zero.
    Available component weights are renormalized to the evidence actually
    present. AI remains optional; when absent, its 15% weight is excluded.
    Returns (None, breakdown) when no scoring evidence is available.
    """

    def _component(value, weight, name):
        score = _safe_float(value)
        if score is None:
            return None
        return _clamp(score), float(weight), name

    components = []

    technical = _component(technical_score, 0.35, "Technical")
    if technical is not None:
        components.append(technical)

    fundamental = _component(fundamental_score, 0.40, "Fundamental")
    if fundamental is not None:
        components.append(fundamental)

    ai_value = None
    if isinstance(ai_result, dict):
        ai_value = ai_result.get("score")
    ai = _component(ai_value, 0.15, "AI")
    if ai is not None:
        components.append(ai)

    stability_score, stability_reasons = calculate_stability_score(
        data if isinstance(data, dict) else {}
    )
    stability = _component(stability_score, 0.10, "Stability")
    if stability is not None:
        components.append(stability)

    if not components:
        return None, {
            "Technical": None,
            "Fundamental": None,
            "AI": None,
            "Stability": None,
            "Technical Contribution": None,
            "Fundamental Contribution": None,
            "AI Contribution": None,
            "Stability Contribution": None,
            "Stability Reasons": stability_reasons,
            "Available Evidence": [],
            "Evidence Weight": 0.0,
        }

    total_weight = sum(weight for _, weight, _ in components)

    # Technical + Fundamental are the core evidence for an investment score.
    # Do not produce a legitimate-looking 0-100 score from only AI/Stability.
    available_names = {name for _, _, name in components}
    if not {"Technical", "Fundamental"}.issubset(available_names):
        return None, {
            "Technical": technical[0] if technical is not None else None,
            "Fundamental": fundamental[0] if fundamental is not None else None,
            "AI": ai[0] if ai is not None else None,
            "Stability": stability[0] if stability is not None else None,
            "Technical Contribution": None,
            "Fundamental Contribution": None,
            "AI Contribution": None,
            "Stability Contribution": None,
            "Stability Reasons": stability_reasons,
            "Available Evidence": [name for _, _, name in components],
            "Evidence Weight": total_weight,
            "Score Status": "INSUFFICIENT CORE EVIDENCE",
        }

    overall = sum(score * weight for score, weight, _ in components) / total_weight
    overall = round(_clamp(overall))

    raw = {name: score for score, _, name in components}
    raw_weights = {name: weight for _, weight, name in components}

    breakdown = {
        "Technical": raw.get("Technical"),
        "Fundamental": raw.get("Fundamental"),
        "AI": raw.get("AI"),
        "Stability": raw.get("Stability"),
        "Technical Contribution": (
            raw["Technical"] * raw_weights["Technical"] / total_weight
            if "Technical" in raw else None
        ),
        "Fundamental Contribution": (
            raw["Fundamental"] * raw_weights["Fundamental"] / total_weight
            if "Fundamental" in raw else None
        ),
        "AI Contribution": (
            raw["AI"] * raw_weights["AI"] / total_weight
            if "AI" in raw else None
        ),
        "Stability Contribution": (
            raw["Stability"] * raw_weights["Stability"] / total_weight
            if "Stability" in raw else None
        ),
        "Stability Reasons": stability_reasons,
        "Available Evidence": [name for _, _, name in components],
        "Evidence Weight": total_weight,
    }

    for key in (
        "Technical Contribution",
        "Fundamental Contribution",
        "AI Contribution",
        "Stability Contribution",
    ):
        if breakdown[key] is not None:
            breakdown[key] = round(breakdown[key], 2)

    return overall, breakdown
