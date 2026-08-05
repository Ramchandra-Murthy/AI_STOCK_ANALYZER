def to_float(value):
    """
    Safely convert values to float.
    Returns None if conversion fails.
    """

    if value is None:
        return None

    if isinstance(value, str):
        value = value.replace("%", "").replace(",", "").strip()

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_fundamental_score(data):

    score = 50
    reasons = []

    pe = to_float(data.get("pe"))
    pb = to_float(data.get("pb"))
    roe = to_float(data.get("roe"))
    margin = to_float(data.get("profit_margin"))
    op_margin = to_float(data.get("operating_margin"))
    beta = to_float(data.get("beta"))
    dividend = to_float(data.get("dividend_yield"))

    # ------------------------
    # PE
    # ------------------------

    if pe is not None:

        if pe < 20:
            score += 10
            reasons.append("Healthy P/E Ratio")

        elif pe > 40:
            score -= 10
            reasons.append("High P/E Ratio")

    # ------------------------
    # PB
    # ------------------------

    if pb is not None:

        if pb < 3:
            score += 5
            reasons.append("Reasonable Price-to-Book")

    # ------------------------
    # ROE
    # ------------------------

    if roe is not None:

        if roe > 20:
            score += 15
            reasons.append("Excellent Return on Equity")

        elif roe > 15:
            score += 10
            reasons.append("Strong Return on Equity")

    # ------------------------
    # Profit Margin
    # ------------------------

    if margin is not None:

        # Yahoo returns decimal values
        # 0.15 = 15%

        if margin > 0.15:
            score += 10
            reasons.append("Healthy Profit Margin")

    # ------------------------
    # Operating Margin
    # ------------------------

    if op_margin is not None:

        if op_margin > 0.20:
            score += 10
            reasons.append("Strong Operating Margin")

    # ------------------------
    # Beta
    # ------------------------

    if beta is not None:

        if beta < 1:
            score += 5
            reasons.append("Lower Market Risk")

    # ------------------------
    # Dividend
    # ------------------------

    if dividend is not None:

        if dividend > 0:
            score += 5
            reasons.append("Dividend Paying Company")

    score = max(0, min(score, 100))

    return score, reasons
