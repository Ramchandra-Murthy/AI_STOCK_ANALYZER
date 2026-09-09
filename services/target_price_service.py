import math

import pandas as pd


def _safe_float(value, default=None):
    """Convert a value to float safely."""

    try:
        number = float(value)

        if math.isnan(number) or math.isinf(number):
            return default

        return number

    except (TypeError, ValueError):
        return default


def calculate_target_price(history, technical_score=None):
    """
    Calculate a rule-based target price, stop loss,
    upside/downside and risk/reward estimate.

    Parameters
    ----------
    history : pandas.DataFrame
        Historical OHLC price data.

    technical_score : float or None
        Technical score between 0 and 100. A missing or invalid score
        is treated as insufficient evidence and never replaced by a
        fabricated neutral score.

    Returns
    -------
    dict
        Trade-planning metrics.
    """

    if history is None or history.empty:
        return {
            "current_price": None,
            "target_price": None,
            "stop_loss": None,
            "upside_percent": None,
            "risk_reward": None,
            "atr": None,
            "status": "No historical data",
        }

    required_columns = {
        "High",
        "Low",
        "Close",
    }

    missing = required_columns.difference(history.columns)

    if missing:
        return {
            "current_price": None,
            "target_price": None,
            "stop_loss": None,
            "upside_percent": None,
            "risk_reward": None,
            "atr": None,
            "status": ("Missing columns: " + ", ".join(sorted(missing))),
        }

    df = history.copy()

    for column in required_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=[
            "High",
            "Low",
            "Close",
        ]
    )

    if df.empty:
        return {
            "current_price": None,
            "target_price": None,
            "stop_loss": None,
            "upside_percent": None,
            "risk_reward": None,
            "atr": None,
            "status": "Price data unavailable",
        }

    # --------------------------------------------------
    # Current Price
    # --------------------------------------------------

    current_price = _safe_float(df["Close"].iloc[-1])

    if current_price is None or current_price <= 0:
        return {
            "current_price": None,
            "target_price": None,
            "stop_loss": None,
            "upside_percent": None,
            "risk_reward": None,
            "atr": None,
            "status": "Invalid current price",
        }

    # --------------------------------------------------
    # ATR
    # --------------------------------------------------

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
        min_periods=1,
    ).mean()

    atr = _safe_float(
        atr_series.iloc[-1],
        0.0,
    )

    if atr is None or atr < 0:
        return {
            "current_price": round(current_price, 2),
            "target_price": None,
            "stop_loss": None,
            "upside_percent": None,
            "risk_reward": None,
            "atr": None,
            "status": "ATR unavailable",
        }

    # --------------------------------------------------
    # Technical Score
    # --------------------------------------------------

    score = _safe_float(technical_score)

    if score is None:
        return {
            "current_price": round(current_price, 2),
            "target_price": None,
            "stop_loss": None,
            "upside_percent": None,
            "risk_reward": None,
            "atr": round(atr, 2),
            "status": "Insufficient technical evidence",
        }

    score = max(
        0.0,
        min(score, 100.0),
    )

    # --------------------------------------------------
    # Target Multiplier
    # --------------------------------------------------

    if score >= 80:
        target_atr_multiplier = 3.0

    elif score >= 65:
        target_atr_multiplier = 2.5

    elif score >= 50:
        target_atr_multiplier = 2.0

    else:
        target_atr_multiplier = 1.5

    # --------------------------------------------------
    # Target / Stop
    # --------------------------------------------------

    target_price = current_price + atr * target_atr_multiplier

    stop_loss = current_price - atr * 1.5

    stop_loss = max(
        stop_loss,
        0.0,
    )

    reward = target_price - current_price

    risk = current_price - stop_loss

    upside_percent = reward / current_price * 100

    risk_reward = reward / risk if risk > 0 else None

    return {
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
        "risk_reward": (round(risk_reward, 2) if risk_reward is not None else None),
        "atr": round(
            atr,
            2,
        ),
        "status": "OK",
    }
