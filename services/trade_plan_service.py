import math

import pandas as pd

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================


def _safe_float(value):
    """Convert a value to a finite float or return None."""

    try:
        value = float(value)

        if math.isnan(value) or math.isinf(value):
            return None

        return value

    except (TypeError, ValueError):
        return None


def _clamp(value, minimum, maximum):
    """Restrict a numeric value to a range."""

    return max(
        minimum,
        min(value, maximum),
    )


# ==========================================================
# TRADE PLAN ENGINE
# ==========================================================


def generate_trade_plan(
    history: pd.DataFrame,
    technical_score: float = 50,
):
    """
    Generate a rule-based trade plan using:

    - Current price
    - 14-period ATR
    - 20-period support/resistance
    - 50-period support/resistance
    - Technical score
    - Trend context
    - Minimum ATR stop distance
    - Risk/reward validation

    This is a research model, not a prediction engine.

    Returns a dictionary compatible with the existing
    Streamlit application and PDF generator.
    """

    # ======================================================
    # VALIDATION
    # ======================================================

    if history is None or history.empty:

        return {
            "status": "ERROR",
            "message": "No historical price data available.",
        }

    df = history.copy()

    required_columns = [
        "High",
        "Low",
        "Close",
    ]

    for column in required_columns:

        if column not in df.columns:

            return {
                "status": "ERROR",
                "message": (f"Missing required column: {column}"),
            }

    df = df.dropna(
        subset=[
            "High",
            "Low",
            "Close",
        ]
    )

    if len(df) < 20:

        return {
            "status": "ERROR",
            "message": "Insufficient historical data.",
        }

    # ======================================================
    # CURRENT PRICE
    # ======================================================

    current_price = _safe_float(df["Close"].iloc[-1])

    if current_price is None or current_price <= 0:

        return {
            "status": "ERROR",
            "message": "Invalid current price.",
        }

    # ======================================================
    # TECHNICAL SCORE
    # ======================================================

    score = _safe_float(technical_score)

    if score is None:
        score = 50.0

    score = _clamp(
        score,
        0.0,
        100.0,
    )

    # ======================================================
    # ATR
    # ======================================================

    previous_close = df["Close"].shift(1)

    true_range = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - previous_close).abs(),
            (df["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr_series = true_range.rolling(
        window=14,
        min_periods=14,
    ).mean()

    atr = _safe_float(atr_series.iloc[-1])

    if atr is None or atr <= 0:

        return {
            "status": "ERROR",
            "message": "Unable to calculate ATR.",
        }

    atr_percent = atr / current_price * 100

    # ======================================================
    # SUPPORT / RESISTANCE
    # ======================================================

    completed = df.iloc[:-1]

    if completed.empty:
        completed = df.copy()

    short_window = completed.tail(20)
    medium_window = completed.tail(50)

    support_20 = _safe_float(short_window["Low"].min())

    resistance_20 = _safe_float(short_window["High"].max())

    support_50 = _safe_float(medium_window["Low"].min())

    resistance_50 = _safe_float(medium_window["High"].max())

    if support_20 is None:

        support_20 = current_price - 2.0 * atr

    if resistance_20 is None:

        resistance_20 = current_price + 2.0 * atr

    if support_50 is None:
        support_50 = support_20

    if resistance_50 is None:
        resistance_50 = resistance_20

    # Main displayed levels.

    support = support_20
    resistance = resistance_20

    # ======================================================
    # TREND CONTEXT
    # ======================================================

    close = df["Close"]

    ema20 = close.ewm(
        span=20,
        adjust=False,
    ).mean()

    ema50 = close.ewm(
        span=50,
        adjust=False,
    ).mean()

    latest_ema20 = _safe_float(ema20.iloc[-1])

    latest_ema50 = _safe_float(ema50.iloc[-1])

    bullish_trend = False
    bearish_trend = False

    if latest_ema20 is not None and latest_ema50 is not None:

        bullish_trend = current_price > latest_ema20 and latest_ema20 > latest_ema50

        bearish_trend = current_price < latest_ema20 and latest_ema20 < latest_ema50

    # ======================================================
    # SIGNAL
    # ======================================================

    if score >= 80:

        signal = "STRONG BUY"
        target_atr_multiplier = 3.0
        stop_atr_multiplier = 1.50

    elif score >= 65:

        signal = "BUY"
        target_atr_multiplier = 2.5
        stop_atr_multiplier = 1.50

    elif score >= 50:

        signal = "HOLD / WATCH"
        target_atr_multiplier = 2.0
        stop_atr_multiplier = 1.50

    elif score >= 35:

        signal = "WEAK / CAUTIOUS"
        target_atr_multiplier = 1.5
        stop_atr_multiplier = 1.75

    else:

        signal = "AVOID / SELL"
        target_atr_multiplier = 1.0
        stop_atr_multiplier = 2.0

    # Weak/bearish setups receive a more conservative
    # upside assumption.

    if bearish_trend:

        target_atr_multiplier = max(
            0.75,
            target_atr_multiplier - 0.25,
        )

    elif bullish_trend:

        target_atr_multiplier += 0.25

    # ======================================================
    # STOP LOSS
    # ======================================================

    # The stop must have a meaningful volatility buffer.
    # Nearby support is NOT allowed to create a tiny stop.

    minimum_risk_distance = atr * stop_atr_multiplier

    atr_stop = current_price - minimum_risk_distance

    # A structural stop is placed below support with a
    # small ATR buffer.

    support_buffer = support - 0.25 * atr

    # Only use structural support when it is reasonably
    # close to current price. Very distant support would
    # create an unnecessarily large risk level.

    distance_to_support = current_price - support

    if support < current_price and distance_to_support <= 2.5 * atr:

        structural_stop = support_buffer

        # Select the lower stop so that support cannot
        # tighten risk below our ATR requirement.

        stop_loss = min(
            atr_stop,
            structural_stop,
        )

    else:

        stop_loss = atr_stop

    stop_loss = max(
        stop_loss,
        0.01,
    )

    risk_per_share = current_price - stop_loss

    if risk_per_share <= 0:

        return {
            "status": "ERROR",
            "message": "Unable to determine valid stop loss.",
        }

    # ======================================================
    # TARGET PRICE
    # ======================================================

    volatility_target = current_price + atr * target_atr_multiplier

    target_price = volatility_target

    # Nearby resistance can serve as a realistic target.
    # Do not use distant historical resistance to inflate
    # the target.

    resistance_distance = resistance - current_price

    if resistance > current_price and resistance_distance <= 3.0 * atr:

        # For weak setups, resistance acts more like a cap.
        if score < 50:

            target_price = min(
                volatility_target,
                resistance,
            )

        else:

            # Stronger setups can target the higher of
            # volatility projection or nearby resistance,
            # but with a sensible ATR cap.

            resistance_cap = current_price + 3.0 * atr

            usable_resistance = min(
                resistance,
                resistance_cap,
            )

            target_price = max(
                volatility_target,
                usable_resistance,
            )

    # Target must remain above current price for the
    # long-side trade-plan representation.

    if target_price <= current_price:

        target_price = current_price + 0.75 * atr

    # ======================================================
    # RISK / REWARD
    # ======================================================

    potential_reward = target_price - current_price

    risk_reward = potential_reward / risk_per_share

    # ======================================================
    # UPSIDE / DOWNSIDE
    # ======================================================

    upside_percent = potential_reward / current_price * 100

    stop_loss_percent = risk_per_share / current_price * 100

    # ======================================================
    # SETUP QUALITY
    # ======================================================

    if score < 35:

        setup_quality = "POOR"

    elif score < 50 or risk_reward < 1.0:

        setup_quality = "WEAK"

    elif score >= 65 and risk_reward >= 1.5 and bullish_trend:

        setup_quality = "STRONG"

    elif risk_reward >= 1.25:

        setup_quality = "ACCEPTABLE"

    else:

        setup_quality = "CAUTIOUS"

    # ======================================================
    # TRADE NOTE
    # ======================================================

    if score < 35:

        trade_note = (
            "Technical conditions are weak. "
            "The calculated levels are primarily "
            "risk-reference levels rather than a "
            "long-entry recommendation."
        )

    elif score < 50:

        trade_note = (
            "Technical conditions remain weak. "
            "Consider waiting for confirmation before "
            "treating the target as an actionable setup."
        )

    elif risk_reward < 1.0:

        trade_note = (
            "The projected reward is smaller than the "
            "estimated risk. The setup is unattractive "
            "on a risk/reward basis."
        )

    else:

        trade_note = (
            "The trade plan is a rule-based technical "
            "scenario derived from volatility, price "
            "structure and technical strength."
        )

    # ======================================================
    # RETURN
    # ======================================================

    return {
        "status": "OK",
        # Existing keys used by your application.
        "current_price": round(
            current_price,
            2,
        ),
        "target_price": round(
            target_price,
            2,
        ),
        "stop_loss": round(
            stop_loss,
            2,
        ),
        "upside_percent": round(
            upside_percent,
            2,
        ),
        "risk_reward": round(
            risk_reward,
            2,
        ),
        "atr": round(
            atr,
            2,
        ),
        "support": round(
            support,
            2,
        ),
        "resistance": round(
            resistance,
            2,
        ),
        "technical_score": round(
            score,
            2,
        ),
        "signal": signal,
        # Additional diagnostic information.
        "setup_quality": setup_quality,
        "trade_note": trade_note,
        "atr_percent": round(
            atr_percent,
            2,
        ),
        "stop_loss_percent": round(
            stop_loss_percent,
            2,
        ),
        "risk_per_share": round(
            risk_per_share,
            2,
        ),
        "support_20": round(
            support_20,
            2,
        ),
        "resistance_20": round(
            resistance_20,
            2,
        ),
        "support_50": round(
            support_50,
            2,
        ),
        "resistance_50": round(
            resistance_50,
            2,
        ),
        "bullish_trend": bullish_trend,
        "bearish_trend": bearish_trend,
    }
