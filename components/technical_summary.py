import math

import streamlit as st

_REQUIRED_COLUMNS = ("Close", "EMA20", "EMA50", "EMA200", "RSI", "MACD", "MACD_Signal")
_OPTIONAL_COLUMNS = ("ATR", "Support", "Resistance", "Volume", "Volume_MA20")


def _finite_number(value):
    """Return a finite float, or None for missing/non-numeric values."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _format_price(value):
    number = _finite_number(value)
    return f"₹{number:.2f}" if number is not None and number > 0 else "N/A"


def show_technical_summary(df, allow_recommendation=True, block_reason=None):
    """
    Display validated technical indicators and optionally withhold recommendations.

    The caller remains responsible for verifying market-data freshness. This
    component validates the latest row but does not claim that data is live.
    """
    st.subheader("📊 Technical Summary")

    if df is None or df.empty:
        st.warning("No technical data available.")
        return

    missing = [column for column in _REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        st.warning(
            "Technical summary unavailable — missing required indicator(s): " + ", ".join(missing)
        )
        return

    latest = df.iloc[-1]
    values = {column: _finite_number(latest[column]) for column in _REQUIRED_COLUMNS}
    invalid = [column for column, value in values.items() if value is None]
    if invalid:
        st.warning(
            "Technical summary unavailable — invalid or missing latest value(s): "
            + ", ".join(invalid)
        )
        return

    price = values["Close"]
    ema20 = values["EMA20"]
    ema50 = values["EMA50"]
    ema200 = values["EMA200"]
    rsi = values["RSI"]
    macd = values["MACD"]
    signal = values["MACD_Signal"]

    if price <= 0 or min(ema20, ema50, ema200) <= 0:
        st.warning("Technical summary unavailable — price and EMA values must be positive.")
        return
    if not 0 <= rsi <= 100:
        st.warning("Technical summary unavailable — RSI must be between 0 and 100.")
        return

    # A mixed EMA structure is not automatically labelled as sideways.
    if price > ema20 > ema50 > ema200:
        trend = "🟢 Strong Uptrend"
    elif price < ema20 < ema50 < ema200:
        trend = "🔴 Strong Downtrend"
    elif price > ema20 and ema20 > ema50:
        trend = "🟢 Bullish Structure"
    elif price < ema20 and ema20 < ema50:
        trend = "🔴 Bearish Structure"
    else:
        trend = "🟡 Mixed"

    if rsi >= 70:
        rsi_text = f"{rsi:.2f} (Overbought)"
    elif rsi <= 30:
        rsi_text = f"{rsi:.2f} (Oversold)"
    else:
        rsi_text = f"{rsi:.2f} (Neutral)"

    macd_text = "🟢 Bullish" if macd > signal else "🔴 Bearish"

    volume = _finite_number(latest["Volume"]) if "Volume" in df.columns else None
    volume_average = _finite_number(latest["Volume_MA20"]) if "Volume_MA20" in df.columns else None
    if volume is None or volume_average is None or volume < 0 or volume_average < 0:
        volume_text = "Unavailable"
    elif volume > volume_average:
        volume_text = "Above Average"
    else:
        volume_text = "Below Average"

    atr = _finite_number(latest["ATR"]) if "ATR" in df.columns else None
    support = _finite_number(latest["Support"]) if "Support" in df.columns else None
    resistance = _finite_number(latest["Resistance"]) if "Resistance" in df.columns else None
    atr_text = f"{atr:.2f}" if atr is not None and atr >= 0 else "N/A"
    support_text = _format_price(support)
    resistance_text = _format_price(resistance)

    score = sum(
        (
            price > ema20,
            ema20 > ema50,
            ema50 > ema200,
            macd > signal,
            50 < rsi < 70,
        )
    )
    if score >= 4:
        recommendation = "🟢 BUY"
    elif score >= 2:
        recommendation = "🟡 HOLD"
    else:
        recommendation = "🔴 SELL"

    c1, c2, c3 = st.columns(3)
    c1.metric("Trend", trend)
    c2.metric("RSI", rsi_text)
    c3.metric("MACD", macd_text)

    c1, c2, c3 = st.columns(3)
    c1.metric("ATR", atr_text)
    c2.metric("Support", support_text)
    c3.metric("Resistance", resistance_text)
    st.metric("Volume", volume_text)

    if allow_recommendation:
        st.success(f"Recommendation: {recommendation}")
    else:
        message = (
            "Recommendation withheld — data freshness is not verified. "
            "Do not use this summary as a current trading signal."
        )
        if block_reason:
            message = f"{message} {block_reason}"
        st.warning(message)
