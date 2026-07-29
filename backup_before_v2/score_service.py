def calculate_investment_score(data, history, ai_result):
    """
    Calculate an overall investment score out of 100.
    """

    score = 0
    breakdown = {}

    # -------------------------------------------------
    # 1. Valuation (20)
    # -------------------------------------------------

    pe = data.get("pe")

    valuation = 10

    try:
        if pe is not None:

            if pe < 20:
                valuation = 20
            elif pe < 30:
                valuation = 16
            elif pe < 40:
                valuation = 12
            else:
                valuation = 8

    except Exception:
        pass

    breakdown["Valuation"] = valuation
    score += valuation

    # -------------------------------------------------
    # 2. Profitability (20)
    # -------------------------------------------------

    roe = data.get("roe")

    profitability = 10

    try:
        if roe is not None:

            roe = roe * 100

            if roe >= 20:
                profitability = 20
            elif roe >= 15:
                profitability = 16
            elif roe >= 10:
                profitability = 12
            else:
                profitability = 8

    except Exception:
        pass

    breakdown["Profitability"] = profitability
    score += profitability

    # -------------------------------------------------
    # 3. Technical (20)
    # -------------------------------------------------

    technical = 15

    if history is not None and not history.empty:

        last = history.iloc[-1]

        if last["Close"] > last["EMA20"]:
            technical += 2

        if last["EMA20"] > last["EMA50"]:
            technical += 2

        if last["RSI"] > 50:
            technical += 1

    breakdown["Technical"] = min(20, technical)
    score += min(20, technical)

    # -------------------------------------------------
    # 4. AI Score (20)
    # -------------------------------------------------

    ai_score = ai_result.get("score", 50)

    ai_points = round(ai_score / 5)

    breakdown["AI"] = ai_points
    score += ai_points

    # -------------------------------------------------
    # 5. Stability (20)
    # -------------------------------------------------

    beta = data.get("beta")

    stability = 15

    try:

        if beta is not None:

            if beta < 1:
                stability = 20
            elif beta < 1.2:
                stability = 18
            elif beta < 1.5:
                stability = 15
            else:
                stability = 10

    except Exception:
        pass

    breakdown["Stability"] = stability
    score += stability

    return score, breakdown
