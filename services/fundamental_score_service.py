import math

# ==========================================================
# HELPERS
# ==========================================================


def to_float(value):
    """
    Safely convert a value to a finite float.
    Returns None when conversion is not possible.
    """

    if value is None:
        return None

    if isinstance(value, str):
        cleaned = (
            value.replace("%", "")
            .replace(",", "")
            .replace("₹", "")
            .replace("Rs.", "")
            .strip()
        )

        if cleaned.upper() in {
            "",
            "N/A",
            "NA",
            "NONE",
            "-",
        }:
            return None

        value = cleaned

    try:
        result = float(value)

        if not math.isfinite(result):
            return None

        return result

    except (TypeError, ValueError):
        return None


def _percent(value):
    """
    Convert Yahoo decimal percentage values to percentage points.

    Example:
        0.15 -> 15.0
    """

    value = to_float(value)

    if value is None:
        return None

    return value * 100.0


def _debt_equity_ratio(value):
    """
    Convert Yahoo debtToEquity to a normal ratio.

    Example:
        36.653 -> 0.36653x
    """

    value = to_float(value)

    if value is None or value < 0:
        return None

    return value / 100.0


def _normalize_category(metric_scores, maximum=20):
    """
    Normalize available metric scores to a category maximum.

    metric_scores:
        [(earned, possible), ...]

    Missing metrics are simply omitted.
    """

    if not metric_scores:
        return None

    earned = sum(item[0] for item in metric_scores)
    possible = sum(item[1] for item in metric_scores)

    if possible <= 0:
        return None

    score = (earned / possible) * maximum

    return max(0.0, min(score, maximum))


# ==========================================================
# FUNDAMENTAL SCORE V2
# ==========================================================


def calculate_fundamental_score(data):
    """
    Fundamental Score V2.

    Categories:
        Valuation          20
        Profitability      20
        Growth             20
        Financial Health   20
        Cash Flow          20

    Total:
        100

    Missing metrics do not automatically receive zero.
    """

    if not isinstance(data, dict):
        return None, ["Fundamental data unavailable."]

    reasons = []

    # ------------------------------------------------------
    # Read and normalize data
    # ------------------------------------------------------

    pe = to_float(data.get("pe"))
    pb = to_float(data.get("pb"))

    roe = _percent(data.get("roe"))
    roa = _percent(data.get("roa"))
    profit_margin = _percent(data.get("profit_margin"))
    operating_margin = _percent(data.get("operating_margin"))

    revenue_growth = _percent(data.get("revenue_growth"))
    earnings_growth = _percent(data.get("earnings_growth"))

    debt_to_equity = _debt_equity_ratio(data.get("debt_to_equity"))

    current_ratio = to_float(data.get("current_ratio"))
    if current_ratio is not None and current_ratio <= 0:
        current_ratio = None

    total_debt = to_float(data.get("total_debt"))
    if total_debt is not None and total_debt < 0:
        total_debt = None

    total_cash = to_float(data.get("total_cash"))
    if total_cash is not None and total_cash < 0:
        total_cash = None

    operating_cash_flow = to_float(data.get("operating_cash_flow"))

    free_cash_flow = to_float(data.get("free_cash_flow"))

    # ======================================================
    # 1. VALUATION — 20
    # ======================================================

    metrics = []

    if pe is not None:

        if 0 < pe <= 15:
            points = 10
            reasons.append(f"P/E of {pe:.2f} indicates attractive valuation.")

        elif pe <= 25:
            points = 8
            reasons.append(f"P/E of {pe:.2f} indicates reasonable valuation.")

        elif pe <= 35:
            points = 5
            reasons.append(f"P/E of {pe:.2f} indicates moderate valuation.")

        elif pe <= 50:
            points = 2
            reasons.append(f"P/E of {pe:.2f} indicates an expensive valuation.")

        else:
            points = 0
            reasons.append(f"P/E of {pe:.2f} indicates a very high valuation.")

        metrics.append((points, 10))

    if pb is not None:

        if 0 < pb <= 1.5:
            points = 10
            reasons.append(
                f"P/B of {pb:.2f} indicates attractive book-value valuation."
            )

        elif pb <= 3:
            points = 8
            reasons.append(f"P/B of {pb:.2f} is reasonable.")

        elif pb <= 5:
            points = 5
            reasons.append(f"P/B of {pb:.2f} is moderately elevated.")

        elif pb <= 8:
            points = 2
            reasons.append(f"P/B of {pb:.2f} is high.")

        else:
            points = 0
            reasons.append(f"P/B of {pb:.2f} indicates a very high valuation.")

        metrics.append((points, 10))

    valuation_score = _normalize_category(metrics)

    # ======================================================
    # 2. PROFITABILITY — 20
    # ======================================================

    metrics = []

    if roe is not None:

        if roe >= 20:
            points = 6
            reasons.append(
                f"ROE of {roe:.2f}% indicates excellent shareholder returns."
            )

        elif roe >= 15:
            points = 5
            reasons.append(f"ROE of {roe:.2f}% indicates strong profitability.")

        elif roe >= 10:
            points = 4
            reasons.append(f"ROE of {roe:.2f}% is healthy.")

        elif roe >= 5:
            points = 2
            reasons.append(f"ROE of {roe:.2f}% indicates modest profitability.")

        else:
            points = 0
            reasons.append(f"ROE of {roe:.2f}% is weak.")

        metrics.append((points, 6))

    if roa is not None:

        if roa >= 10:
            points = 4
            reasons.append(f"ROA of {roa:.2f}% indicates strong asset efficiency.")

        elif roa >= 5:
            points = 3
            reasons.append(f"ROA of {roa:.2f}% indicates healthy asset efficiency.")

        elif roa >= 2:
            points = 2
            reasons.append(f"ROA of {roa:.2f}% indicates moderate asset efficiency.")

        elif roa > 0:
            points = 1
            reasons.append(f"ROA of {roa:.2f}% is positive but low.")

        else:
            points = 0
            reasons.append(f"ROA of {roa:.2f}% is weak.")

        metrics.append((points, 4))

    if profit_margin is not None:

        if profit_margin >= 20:
            points = 5
        elif profit_margin >= 10:
            points = 4
        elif profit_margin >= 5:
            points = 3
        elif profit_margin > 0:
            points = 1
        else:
            points = 0

        metrics.append((points, 5))

        reasons.append(f"Net profit margin is {profit_margin:.2f}%.")

    if operating_margin is not None:

        if operating_margin >= 25:
            points = 5
        elif operating_margin >= 15:
            points = 4
        elif operating_margin >= 10:
            points = 3
        elif operating_margin > 0:
            points = 1
        else:
            points = 0

        metrics.append((points, 5))

        reasons.append(f"Operating margin is {operating_margin:.2f}%.")

    profitability_score = _normalize_category(metrics)

    # ======================================================
    # 3. GROWTH — 20
    # ======================================================

    metrics = []

    if revenue_growth is not None:

        if revenue_growth >= 20:
            points = 10
            reasons.append(f"Revenue growth of {revenue_growth:.2f}% is strong.")

        elif revenue_growth >= 10:
            points = 8
            reasons.append(f"Revenue growth of {revenue_growth:.2f}% is healthy.")

        elif revenue_growth >= 5:
            points = 6
            reasons.append(f"Revenue growth of {revenue_growth:.2f}% is moderate.")

        elif revenue_growth >= 0:
            points = 4
            reasons.append(f"Revenue growth of {revenue_growth:.2f}% is modest.")

        else:
            points = 0
            reasons.append(f"Revenue declined {abs(revenue_growth):.2f}%.")

        metrics.append((points, 10))

    if earnings_growth is not None:

        if earnings_growth >= 20:
            points = 10
            reasons.append(f"Earnings growth of {earnings_growth:.2f}% is strong.")

        elif earnings_growth >= 10:
            points = 8
            reasons.append(f"Earnings growth of {earnings_growth:.2f}% is healthy.")

        elif earnings_growth >= 5:
            points = 6
            reasons.append(f"Earnings growth of {earnings_growth:.2f}% is moderate.")

        elif earnings_growth >= 0:
            points = 4
            reasons.append(f"Earnings growth of {earnings_growth:.2f}% is modest.")

        else:
            points = 0
            reasons.append(f"Earnings declined {abs(earnings_growth):.2f}%.")

        metrics.append((points, 10))

    growth_score = _normalize_category(metrics)

    # ======================================================
    # 4. FINANCIAL HEALTH — 20
    # ======================================================

    metrics = []

    if debt_to_equity is not None:

        if debt_to_equity <= 0.30:
            points = 8
            reasons.append(
                f"Debt-to-equity of {debt_to_equity:.2f}x indicates low leverage."
            )

        elif debt_to_equity <= 0.75:
            points = 7
            reasons.append(
                f"Debt-to-equity of {debt_to_equity:.2f}x indicates manageable leverage."
            )

        elif debt_to_equity <= 1.50:
            points = 5
            reasons.append(f"Debt-to-equity of {debt_to_equity:.2f}x is moderate.")

        elif debt_to_equity <= 2:
            points = 3
            reasons.append(f"Debt-to-equity of {debt_to_equity:.2f}x is elevated.")

        else:
            points = 0
            reasons.append(
                f"Debt-to-equity of {debt_to_equity:.2f}x indicates high leverage."
            )

        metrics.append((points, 8))

    if current_ratio is not None:

        if 1.5 <= current_ratio <= 3:
            points = 7
            reasons.append(
                f"Current ratio of {current_ratio:.2f}x indicates healthy liquidity."
            )

        elif 1 <= current_ratio < 1.5:
            points = 5
            reasons.append(
                f"Current ratio of {current_ratio:.2f}x indicates adequate liquidity."
            )

        elif current_ratio > 3:
            points = 5
            reasons.append(
                f"Current ratio of {current_ratio:.2f}x indicates strong liquidity."
            )

        elif current_ratio >= 0.75:
            points = 2
            reasons.append(
                f"Current ratio of {current_ratio:.2f}x indicates tight liquidity."
            )

        else:
            points = 0
            reasons.append(
                f"Current ratio of {current_ratio:.2f}x indicates weak liquidity."
            )

        metrics.append((points, 7))

    if total_cash is not None and total_debt is not None:

        if total_debt <= 0:
            points = 5
            reasons.append("The company reports little or no financial debt.")

        else:
            cash_debt_ratio = total_cash / total_debt

            if cash_debt_ratio >= 1:
                points = 5
                reasons.append("Cash is sufficient to cover reported debt.")

            elif cash_debt_ratio >= 0.50:
                points = 4
                reasons.append(
                    f"Cash covers approximately {cash_debt_ratio * 100:.1f}% of debt."
                )

            elif cash_debt_ratio >= 0.25:
                points = 2
                reasons.append(
                    f"Cash covers approximately {cash_debt_ratio * 100:.1f}% of debt."
                )

            else:
                points = 0
                reasons.append("Cash coverage of debt is relatively low.")

        metrics.append((points, 5))

    health_score = _normalize_category(metrics)

    # ======================================================
    # 5. CASH FLOW — 20
    # ======================================================

    metrics = []

    if operating_cash_flow is not None:

        if operating_cash_flow > 0:
            points = 10
            reasons.append("Operating cash flow is positive.")

        elif operating_cash_flow == 0:
            points = 3
            reasons.append("Operating cash flow is approximately neutral.")

        else:
            points = 0
            reasons.append("Operating cash flow is negative.")

        metrics.append((points, 10))

    if free_cash_flow is not None:

        if free_cash_flow > 0:
            points = 10
            reasons.append("Free cash flow is positive.")

        elif free_cash_flow == 0:
            points = 3
            reasons.append("Free cash flow is approximately neutral.")

        else:
            points = 0
            reasons.append("Free cash flow is negative.")

        metrics.append((points, 10))

    cash_flow_score = _normalize_category(metrics)

    # ======================================================
    # FINAL SCORE
    # ======================================================

    category_scores = [
        valuation_score,
        profitability_score,
        growth_score,
        health_score,
        cash_flow_score,
    ]

    available_scores = [score for score in category_scores if score is not None]

    if not available_scores:
        return None, ["Insufficient fundamental data to calculate a score."]

    # Each category is normalized to 20.
    # Average category score * 5 gives a 0-100 result.

    final_score = (sum(available_scores) / len(available_scores)) * 5

    final_score = round(
        max(
            0,
            min(final_score, 100),
        )
    )

    return final_score, reasons
