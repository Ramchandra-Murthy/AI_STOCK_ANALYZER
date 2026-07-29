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
    """
    Calculate Investment Score V2.

    Weighting
    ---------
    Technical Score       35%
    Fundamental Score V2  40%
    AI Score              15%
    Stability / Risk      10%

    Total                 100%

    Returns
    -------
    investment_score : int
        Final score from 0 to 100.

    breakdown : dict
        Detailed component scores and weighted
        contributions.
    """

    # ------------------------------------------------------
    # Technical score
    # ------------------------------------------------------

    technical = _safe_float(technical_score)

    if technical is None:
        technical = 50.0

    technical = _clamp(technical)

    # ------------------------------------------------------
    # Fundamental score
    # ------------------------------------------------------

    fundamental = _safe_float(fundamental_score)

    if fundamental is None:
        fundamental = 50.0

    fundamental = _clamp(fundamental)

    # ------------------------------------------------------
    # AI score
    # ------------------------------------------------------

    ai_score = None

    if isinstance(ai_result, dict):
        ai_score = _safe_float(ai_result.get("score"))

    if ai_score is None:
        ai_score = 50.0

    ai_score = _clamp(ai_score)

    # ------------------------------------------------------
    # Stability score
    # ------------------------------------------------------

    stability_score, stability_reasons = calculate_stability_score(
        data if isinstance(data, dict) else {}
    )

    stability_score = _clamp(stability_score)

    # ------------------------------------------------------
    # Weighted contributions
    # ------------------------------------------------------

    technical_contribution = technical * 0.35

    fundamental_contribution = fundamental * 0.40

    ai_contribution = ai_score * 0.15

    stability_contribution = stability_score * 0.10

    overall = (
        technical_contribution
        + fundamental_contribution
        + ai_contribution
        + stability_contribution
    )

    overall = round(_clamp(overall))

    # ------------------------------------------------------
    # Breakdown
    # ------------------------------------------------------

    breakdown = {
        "Technical": round(
            technical,
            2,
        ),
        "Fundamental": round(
            fundamental,
            2,
        ),
        "AI": round(
            ai_score,
            2,
        ),
        "Stability": round(
            stability_score,
            2,
        ),
        "Technical Contribution": round(
            technical_contribution,
            2,
        ),
        "Fundamental Contribution": round(
            fundamental_contribution,
            2,
        ),
        "AI Contribution": round(
            ai_contribution,
            2,
        ),
        "Stability Contribution": round(
            stability_contribution,
            2,
        ),
        "Stability Reasons": stability_reasons,
    }

    return overall, breakdown
