import math

import pandas as pd


def _safe_float(value):
    """Convert a value to a finite float or return None."""
    try:
        value = float(value)

        if math.isnan(value) or math.isinf(value):
            return None

        return value

    except (TypeError, ValueError):
        return None


def generate_trade_plan(
    history: pd.DataFrame,
    technical_score: float = 50,
):
    """
    Generate a rule-based trade plan from historical price data.

    Returns:
        {
            "status": "OK",
            "current_price": ...,
            "target_price": ...,
            "stop_loss": ...,
            "upside_percent": ...,
            "risk_reward": ...,
            "atr": ...,
            "support": ...,
            "resistance": ...,
            "signal": ...
        }
    """

    # ------------------------------------------------------
    # Validate data
    # ------------------------------------------------------

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
                "message": f"Missing required column: {column}",
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

    # ------------------------------------------------------
    # Current price
    # ------------------------------------------------------

    current_price = _safe_float(df["Close"].iloc[-1])

    if current_price is None or current_price <= 0:
        return {
            "status": "ERROR",
            "message": "Invalid current price.",
        }

    # ------------------------------------------------------
    # ATR - 14 periods
    # ------------------------------------------------------

    previous_close = df["Close"].shift(1)

    true_range = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - previous_close).abs(),
            (df["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr_series = true_range.rolling(window=14).mean()

    atr = _safe_float(atr_series.iloc[-1])

    if atr is None or atr <= 0:
        return {
            "status": "ERROR",
            "message": "Unable to calculate ATR.",
        }

    # ------------------------------------------------------
    # Support and resistance
    # Last 20 completed candles, excluding current candle
    # ------------------------------------------------------

    previous_data = df.iloc[:-1].tail(20)

    if previous_data.empty:
        previous_data = df.tail(20)

    support = _safe_float(previous_data["Low"].min())

    resistance = _safe_float(previous_data["High"].max())

    if support is None:
        support = current_price - (2 * atr)

    if resistance is None:
        resistance = current_price + (2 * atr)

    # ------------------------------------------------------
    # Technical-score-based target multiplier
    # ------------------------------------------------------

    score = _safe_float(technical_score)

    if score is None:
        score = 50.0

    score = max(
        0.0,
        min(score, 100.0),
    )

    if score >= 80:
        target_atr_multiplier = 3.0
        signal = "STRONG BUY"

    elif score >= 65:
        target_atr_multiplier = 2.5
        signal = "BUY"

    elif score >= 50:
        target_atr_multiplier = 2.0
        signal = "HOLD / WATCH"

    elif score >= 35:
        target_atr_multiplier = 1.5
        signal = "WEAK / CAUTIOUS"

    else:
        target_atr_multiplier = 1.0
        signal = "AVOID / SELL"

    # ------------------------------------------------------
    # Target price
    # ------------------------------------------------------

    volatility_target = current_price + atr * target_atr_multiplier

    # Resistance is useful as a reference, but don't let an
    # old distant resistance create an unrealistic target.
    resistance_cap = current_price + atr * (target_atr_multiplier + 1.0)

    usable_resistance = min(
        resistance,
        resistance_cap,
    )

    if usable_resistance > current_price:
        target_price = max(
            volatility_target,
            usable_resistance,
        )
    else:
        target_price = volatility_target

    # ------------------------------------------------------
    # Stop loss
    # ------------------------------------------------------

    volatility_stop = current_price - 1.5 * atr

    # Use nearby support where practical.
    if support < current_price:
        stop_loss = max(
            volatility_stop,
            support,
        )
    else:
        stop_loss = volatility_stop

    stop_loss = max(
        stop_loss,
        0.01,
    )

    # ------------------------------------------------------
    # Risk / reward
    # ------------------------------------------------------

    potential_reward = target_price - current_price

    potential_risk = current_price - stop_loss

    if potential_risk > 0:
        risk_reward = potential_reward / potential_risk
    else:
        risk_reward = None

    # ------------------------------------------------------
    # Upside
    # ------------------------------------------------------

    upside_percent = (target_price - current_price) / current_price * 100

    # ------------------------------------------------------
    # Return plan
    # ------------------------------------------------------

    return {
        "status": "OK",
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
        "risk_reward": (
            round(
                risk_reward,
                2,
            )
            if risk_reward is not None
            else None
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
    }
