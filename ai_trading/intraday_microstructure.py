"""Intraday market-microstructure proxies derived from OHLCV bars.

These features are bar-based estimates, not substitutes for quote, trade, or
Level-2 order-book data. In particular, this module does not estimate the
quoted bid-ask spread or queue position.
"""

from __future__ import annotations  # noqa: I001

import math

import numpy as np
import pandas as pd

_REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


def intraday_microstructure_features(
    bars: pd.DataFrame,
    *,
    window: int = 20,
) -> pd.DataFrame:
    """Calculate rolling OHLCV-based volatility, volume and illiquidity proxies.

    Args:
        bars: Time-ordered OHLCV bars. The index is preserved; timestamps are
            not inferred or resampled.
        window: Number of bars in each rolling lookback window.

    Returns:
        A copy of the valid input bars with:
        - log_return: close-to-close log return.
        - range_pct: high-low range divided by close.
        - realized_variance: rolling sum of squared log returns.
        - realized_volatility: square root of rolling realized variance.
        - parkinson_volatility: rolling Parkinson range-volatility estimate.
        - turnover: close multiplied by volume.
        - amihud_illiquidity: rolling mean of absolute return per unit turnover.
        - volume_zscore: current volume standardized against the *prior* window.

    Missing OHLCV rows are removed. Invalid prices, OHLC relationships, negative
    volume, non-finite values, or an invalid window raise ValueError. Rolling
    features remain NaN until a complete lookback window is available.
    """
    if isinstance(window, (bool, np.bool_)) or not isinstance(window, (int, np.integer)):
        raise ValueError("window must be an integer of at least 2")
    if window < 2:
        raise ValueError("window must be an integer of at least 2")
    if not isinstance(bars, pd.DataFrame):
        raise ValueError("bars must be a pandas DataFrame")

    missing = [column for column in _REQUIRED_COLUMNS if column not in bars.columns]
    if missing:
        raise ValueError(f"bars must contain OHLCV columns: {', '.join(missing)}")

    frame = bars.loc[:, _REQUIRED_COLUMNS].copy()
    for column in _REQUIRED_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=list(_REQUIRED_COLUMNS))
    if frame.empty:
        raise ValueError("bars must contain at least one complete OHLCV row")

    values = frame.loc[:, _REQUIRED_COLUMNS].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("OHLCV values must be finite")
    if (frame[["Open", "High", "Low", "Close"]] <= 0.0).any().any():
        raise ValueError("OHLC prices must be positive")
    if (frame["Volume"] < 0.0).any():
        raise ValueError("Volume must be non-negative")
    if (frame["High"] < frame[["Open", "Low", "Close"]].max(axis=1)).any() or (
        frame["Low"] > frame[["Open", "High", "Close"]].min(axis=1)
    ).any():
        raise ValueError("each bar must satisfy Low <= Open/Close <= High")

    close = frame["Close"]
    log_return = np.log(close / close.shift(1))
    log_range = np.log(frame["High"] / frame["Low"])
    parkinson_variance = log_range.pow(2) / (4.0 * math.log(2.0))
    turnover = close * frame["Volume"]

    frame["log_return"] = log_return
    frame["range_pct"] = (frame["High"] - frame["Low"]) / close
    frame["realized_variance"] = log_return.pow(2).rolling(window=window, min_periods=window).sum()
    frame["realized_volatility"] = np.sqrt(frame["realized_variance"])
    frame["parkinson_volatility"] = np.sqrt(
        parkinson_variance.rolling(window=window, min_periods=window).mean()
    )
    frame["turnover"] = turnover

    illiquidity = log_return.abs().div(turnover.where(turnover > 0.0))
    frame["amihud_illiquidity"] = illiquidity.rolling(window=window, min_periods=window).mean()

    prior_volume = frame["Volume"].shift(1)
    prior_mean = prior_volume.rolling(window=window, min_periods=window).mean()
    prior_std = prior_volume.rolling(window=window, min_periods=window).std(ddof=0)
    frame["volume_zscore"] = (frame["Volume"] - prior_mean).div(prior_std.where(prior_std > 0.0))
    return frame
