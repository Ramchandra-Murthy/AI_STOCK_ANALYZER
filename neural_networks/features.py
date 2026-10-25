"""Research-only neural-network experiments for AI_STOCK_ANALYZER."""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


def build_features(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Build causal features from daily OHLCV history."""
    missing = [column for column in REQUIRED_COLUMNS if column not in ohlcv.columns]
    if missing:
        raise ValueError("Missing required OHLCV columns: " + ", ".join(missing))
    frame = ohlcv.loc[:, REQUIRED_COLUMNS].copy().sort_index()
    close = pd.to_numeric(frame["Close"], errors="coerce").astype(float)
    volume = pd.to_numeric(frame["Volume"], errors="coerce").astype(float)
    returns = close.pct_change(fill_method=None)
    features = pd.DataFrame(index=frame.index)
    features["return_1d"] = returns
    features["return_5d"] = close.pct_change(5, fill_method=None)
    features["return_20d"] = close.pct_change(20, fill_method=None)
    features["volatility_20d"] = returns.rolling(20, min_periods=20).std()
    volume_mean = volume.rolling(20, min_periods=20).mean().replace(0, float("nan"))
    features["relative_volume_20d"] = volume / volume_mean
    high = pd.to_numeric(frame["High"], errors="coerce")
    low = pd.to_numeric(frame["Low"], errors="coerce")
    features["range_pct"] = (high - low) / close.replace(0, float("nan"))
    return features.replace([float("inf"), float("-inf")], float("nan"))


def build_direction_dataset(
    ohlcv: pd.DataFrame, horizon: int = 5
) -> tuple[pd.DataFrame, pd.Series]:
    """Build features and future-positive-return labels."""
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    frame = ohlcv.sort_index().copy()
    features = build_features(frame)
    close = pd.to_numeric(frame["Close"], errors="coerce").astype(float)
    future_return = close.shift(-horizon) / close - 1.0
    valid = features.notna().all(axis=1) & future_return.notna() & close.gt(0)
    target = future_return.loc[valid].gt(0).astype("int8")
    return features.loc[valid], target
