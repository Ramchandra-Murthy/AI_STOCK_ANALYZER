def generate_signal(df):

    last = df.iloc[-1]

    score = 50          # Neutral starting score
    reasons = []
    risk = "Medium"

    # =====================================
    # SMA Trend
    # =====================================

    if last["SMA_20"] > last["SMA_50"]:
        score += 15
        reasons.append("20 SMA above 50 SMA (Bullish)")
    else:
        score -= 15
        reasons.append("20 SMA below 50 SMA (Bearish)")

    # =====================================
    # EMA
    # =====================================

    if last["EMA_20"] > last["SMA_20"]:
        score += 10
        reasons.append("EMA20 above SMA20")
    else:
        score -= 10
        reasons.append("EMA20 below SMA20")

    # =====================================
    # RSI
    # =====================================

    rsi = last["RSI_14"]

    if rsi < 30:
        score += 20
        reasons.append("RSI Oversold")

    elif 30 <= rsi <= 45:
        score += 10
        reasons.append("RSI Bullish Zone")

    elif 45 < rsi < 60:
        score += 5
        reasons.append("RSI Neutral")

    elif 60 <= rsi < 70:
        score -= 5
        reasons.append("RSI Slightly Overbought")

    else:
        score -= 20
        reasons.append("RSI Overbought")

    # =====================================
    # MACD
    # =====================================

    if last["MACD"] > last["Signal"]:
        score += 15
        reasons.append("MACD Bullish Crossover")
    else:
        score -= 15
        reasons.append("MACD Bearish Crossover")

    # =====================================
    # Bollinger Bands
    # =====================================

    if last["Close"] < last["BB_Lower"]:
        score += 10
        reasons.append("Price below Lower Bollinger Band")

    elif last["Close"] > last["BB_Upper"]:
        score -= 10
        reasons.append("Price above Upper Bollinger Band")

    # =====================================
    # Support / Resistance
    # =====================================

    if "Support" in last.index:

        if last["Close"] <= last["Support"] * 1.02:
            score += 10
            reasons.append("Trading near Support")

    if "Resistance" in last.index:

        if last["Close"] >= last["Resistance"] * 0.98:
            score -= 10
            reasons.append("Trading near Resistance")

    # =====================================
    # ATR Risk
    # =====================================

    if "ATR" in last.index:

        atr_percent = (last["ATR"] / last["Close"]) * 100

        if atr_percent > 5:
            risk = "High"
            score -= 5
            reasons.append("High Volatility")

        elif atr_percent < 2:
            risk = "Low"
            score += 5
            reasons.append("Low Volatility")

        else:
            risk = "Medium"

    # =====================================
    # Clamp Score
    # =====================================

    score = max(0, min(score, 100))

    # =====================================
    # Recommendation
    # =====================================

    if score >= 85:
        recommendation = "STRONG BUY"

    elif score >= 70:
        recommendation = "BUY"

    elif score >= 45:
        recommendation = "HOLD"

    elif score >= 25:
        recommendation = "SELL"

    else:
        recommendation = "STRONG SELL"

    # =====================================
    # Confidence
    # =====================================

    confidence = score if score >= 50 else 100 - score

    return {

        "Score": score,

        "Confidence": round(confidence, 1),

        "Recommendation": recommendation,

        "Risk": risk,

        "Reasons": reasons

    }