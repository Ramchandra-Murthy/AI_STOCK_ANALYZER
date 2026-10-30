"""Research-only rolling z-score mean-reversion signal workflow."""

from __future__ import annotations

import numpy as np
import pandas as pd


def mean_reversion_signals(
    spread: pd.Series,
    *,
    lookback: int = 20,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
) -> pd.DataFrame:
    """Build causal long/short spread signals and next-bar positions.

    Rolling statistics use observations available at each timestamp.
    The position column is shifted one row to model next-bar alignment.

    Position values are +1 (long spread), -1 (short spread), or 0 (flat).
    """
    if lookback < 2:
        raise ValueError("lookback must be at least 2")
    if not np.isfinite(entry_z) or entry_z <= 0.0:
        raise ValueError("entry_z must be finite and positive")
    if not np.isfinite(exit_z) or exit_z < 0.0 or exit_z >= entry_z:
        raise ValueError("exit_z must be finite and in [0, entry_z)")

    numeric = pd.to_numeric(spread, errors="coerce")
    clean = numeric.where(np.isfinite(numeric.to_numpy(dtype=float)))
    rolling_mean = clean.rolling(lookback, min_periods=lookback).mean()
    rolling_std = clean.rolling(lookback, min_periods=lookback).std(ddof=1)
    zscore = (clean - rolling_mean) / rolling_std.replace(0.0, np.nan)

    raw_position = np.zeros(len(clean), dtype=int)
    current = 0
    z_values = zscore.to_numpy(dtype=float)
    for index, z_value in enumerate(z_values):
        if not np.isfinite(z_value):
            current = 0
        elif current == 0:
            if z_value <= -entry_z:
                current = 1
            elif z_value >= entry_z:
                current = -1
        elif abs(z_value) <= exit_z:
            current = 0
        raw_position[index] = current

    return pd.DataFrame(
        {
            "spread": clean,
            "rolling_mean": rolling_mean,
            "rolling_std": rolling_std,
            "zscore": zscore,
            "signal": raw_position,
            "position": pd.Series(raw_position, index=clean.index).shift(1).fillna(0).astype(int),
        },
        index=clean.index,
    )


def price_mean_reversion_signals(
    close: pd.Series,
    *,
    lookback: int = 20,
    rsi_period: int = 14,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    oversold_rsi: float = 35.0,
    overbought_rsi: float = 65.0,
    allow_short: bool = False,
) -> pd.DataFrame:
    """Generate price mean-reversion candidates with RSI reversal confirmation.

    Long entries require a negative Z-score at or below the entry threshold,
    RSI below the oversold threshold, and improving RSI versus the prior bar.
    Optional short entries mirror those conditions. Signals use completed
    bars; position is shifted one bar to avoid same-bar execution bias.
    This is research output, not a broker order or profitability claim.
    """
    if isinstance(lookback, bool) or not isinstance(lookback, int) or lookback < 2:
        raise ValueError("lookback must be an integer of at least 2")
    if isinstance(rsi_period, bool) or not isinstance(rsi_period, int) or rsi_period < 2:
        raise ValueError("rsi_period must be an integer of at least 2")
    if not np.isfinite(entry_z) or entry_z <= 0.0:
        raise ValueError("entry_z must be finite and positive")
    if not np.isfinite(exit_z) or exit_z < 0.0 or exit_z >= entry_z:
        raise ValueError("exit_z must be finite and in [0, entry_z)")
    if not 0.0 < oversold_rsi < overbought_rsi < 100.0:
        raise ValueError("RSI thresholds must satisfy 0 < oversold < overbought < 100")

    prices = pd.to_numeric(close, errors="coerce").astype(float)
    finite = prices.dropna()
    if len(finite) < max(lookback, rsi_period) + 1:
        raise ValueError("insufficient valid closing prices")
    if not np.isfinite(finite.to_numpy()).all() or (finite <= 0.0).any():
        raise ValueError("closing prices must be finite and positive")

    mean = prices.rolling(lookback, min_periods=lookback).mean()
    std = prices.rolling(lookback, min_periods=lookback).std(ddof=0)
    zscore = (prices - mean) / std.replace(0.0, np.nan)

    change = prices.diff()
    gain = change.clip(lower=0.0)
    loss = -change.clip(upper=0.0)
    avg_gain = gain.rolling(rsi_period, min_periods=rsi_period).mean()
    avg_loss = loss.rolling(rsi_period, min_periods=rsi_period).mean()
    relative_strength = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + relative_strength))
    rsi = rsi.mask((avg_loss == 0.0) & (avg_gain > 0.0), 100.0)
    rsi = rsi.mask((avg_loss == 0.0) & (avg_gain == 0.0), 50.0)

    improving = rsi > rsi.shift(1)
    weakening = rsi < rsi.shift(1)
    long_entry = (zscore <= -entry_z) & (rsi < oversold_rsi) & improving
    short_entry = (zscore >= entry_z) & (rsi > overbought_rsi) & weakening
    if not allow_short:
        short_entry = pd.Series(False, index=prices.index)

    raw_signal = pd.Series(0, index=prices.index, dtype=int)
    raw_signal.loc[long_entry.fillna(False)] = 1
    raw_signal.loc[short_entry.fillna(False)] = -1
    raw_position = 0
    positions: list[int] = []
    for z_value, signal in zip(zscore.to_numpy(), raw_signal.to_numpy()):
        if not np.isfinite(z_value):
            raw_position = 0
        elif raw_position == 0 and signal != 0:
            raw_position = int(signal)
        elif raw_position == 1 and z_value >= -exit_z:
            raw_position = 0
        elif raw_position == -1 and z_value <= exit_z:
            raw_position = 0
        positions.append(raw_position)

    return pd.DataFrame(
        {
            "close": prices,
            "rolling_mean": mean,
            "rolling_std": std,
            "zscore": zscore,
            "rsi": rsi,
            "long_entry": long_entry.fillna(False),
            "short_entry": short_entry.fillna(False),
            "signal": raw_signal,
            "position": pd.Series(positions, index=prices.index).shift(1).fillna(0).astype(int),
            "signal_scope": "research_only_next_bar_execution",
        },
        index=prices.index,
    )
