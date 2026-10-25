"""Research-only neural-network experiments for AI_STOCK_ANALYZER."""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


def build_features(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Build causal, price/volume-derived factors from daily OHLCV history.

    Feature families adapt the Cookbook's factor-engineering approach to a
    single-stock daily dataset. All rolling statistics use current/past rows
    only; forward returns belong exclusively in the target.
    """
    missing = [column for column in REQUIRED_COLUMNS if column not in ohlcv.columns]
    if missing:
        raise ValueError("Missing required OHLCV columns: " + ", ".join(missing))
    frame = ohlcv.loc[:, REQUIRED_COLUMNS].copy().sort_index()
    close = pd.to_numeric(frame["Close"], errors="coerce").astype(float)
    high = pd.to_numeric(frame["High"], errors="coerce").astype(float)
    low = pd.to_numeric(frame["Low"], errors="coerce").astype(float)
    volume = pd.to_numeric(frame["Volume"], errors="coerce").astype(float)
    returns = close.pct_change(fill_method=None)

    features = pd.DataFrame(index=frame.index)
    # Momentum and realized-risk factors.
    features["return_1d"] = returns
    features["return_5d"] = close.pct_change(5, fill_method=None)
    features["return_20d"] = close.pct_change(20, fill_method=None)
    features["volatility_20d"] = returns.rolling(20, min_periods=20).std()

    # Trend factor: distance from the trailing 20-session mean, scaled by price.
    sma_20 = close.rolling(20, min_periods=20).mean()
    features["sma_distance_20d"] = close / sma_20 - 1.0

    # Relative volume and rolling volume surprise.
    volume_mean = volume.rolling(20, min_periods=20).mean()
    volume_std = volume.rolling(20, min_periods=20).std().replace(0, float("nan"))
    features["relative_volume_20d"] = volume / volume_mean.replace(0, float("nan"))
    features["volume_zscore_20d"] = (volume - volume_mean) / volume_std

    # RSI-like bounded momentum factor, calculated from trailing price changes.
    change = close.diff()
    gains = change.clip(lower=0).ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    losses = -change.clip(upper=0).ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    relative_strength = gains / losses.replace(0, float("nan"))
    rsi = 100.0 - 100.0 / (1.0 + relative_strength)
    features["rsi_14"] = rsi.where(losses.ne(0), 100.0)

    # ATR-normalized daily range factor; the rolling window is backward-looking.
    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr_14 = true_range.rolling(14, min_periods=14).mean()
    features["atr_pct_14"] = atr_14 / close.replace(0, float("nan"))
    features["range_pct"] = (high - low) / close.replace(0, float("nan"))

    return features.replace([float("inf"), float("-inf")], float("nan"))


def build_direction_dataset(
    ohlcv: pd.DataFrame, horizon: int = 5
) -> tuple[pd.DataFrame, pd.Series]:
    """Build causal features and future-positive-return labels."""
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    frame = ohlcv.sort_index().copy()
    features = build_features(frame)
    close = pd.to_numeric(frame["Close"], errors="coerce").astype(float)
    # Match the backtest: signal after close[t], enter at close[t+1], exit at close[t+horizon+1].
    entry_close = close.shift(-1)
    exit_close = close.shift(-(horizon + 1))
    future_return = exit_close / entry_close - 1.0
    valid = (
        features.notna().all(axis=1)
        & future_return.notna()
        & entry_close.gt(0)
        & exit_close.gt(0)
        & close.gt(0)
    )
    target = future_return.loc[valid].gt(0).astype("int8")
    return features.loc[valid], target
