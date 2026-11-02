"""Return autocorrelation diagnostics for research backtests."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _validate_lag(lag: int) -> None:
    if isinstance(lag, (bool, np.bool_)) or not isinstance(lag, (int, np.integer)):
        raise ValueError("lag must be an integer")
    if lag < 1:
        raise ValueError("lag must be at least 1")


def return_autocorrelation(
    returns: pd.Series,
    *,
    lag: int = 1,
) -> float | None:
    """Measure serial dependence in strategy returns at a selected lag."""
    _validate_lag(lag)

    clean = pd.to_numeric(returns, errors="coerce").dropna()
    if not np.isfinite(clean.to_numpy(dtype=float)).all():
        raise ValueError("returns must contain only finite numeric values")
    if len(clean) <= lag:
        return None

    value = clean.autocorr(lag=lag)
    return float(value) if pd.notna(value) else None


def return_autocorrelation_summary(
    returns: pd.Series,
    *,
    lags: tuple[int, ...] = (1, 2, 5, 10),
) -> dict[str, float | None]:
    """Summarize serial dependence across selected return lags."""
    if not lags:
        raise ValueError("lags must contain at least one value")
    for lag in lags:
        _validate_lag(lag)

    return {f"lag_{lag}": return_autocorrelation(returns, lag=lag) for lag in lags}
