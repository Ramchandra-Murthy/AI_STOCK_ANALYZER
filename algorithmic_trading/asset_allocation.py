"""Asset-allocation utilities for NSE/BSE portfolio research.

Adapted from the allocation concepts covered in Chapter 9 of Laurent Bernut's
*Algorithmic Short Selling with Python, Second Edition*. These functions
provide transparent allocation baselines rather than declaring one method
universally optimal.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def equal_weight(returns: pd.DataFrame) -> pd.Series:
    """Allocate equally across assets with available return history."""
    if returns.empty:
        return pd.Series(dtype=float)
    columns = list(returns.columns)
    return pd.Series(1.0 / len(columns), index=columns, dtype=float)


def inverse_volatility_weight(
    returns: pd.DataFrame,
    annualization: int = 252,
) -> pd.Series:
    """Allocate inversely to realized annualized volatility."""
    if returns.empty:
        return pd.Series(dtype=float)
    if annualization <= 0:
        raise ValueError("annualization must be greater than zero")

    volatility = returns.std(ddof=1) * np.sqrt(annualization)
    inverse = volatility.replace([np.inf, -np.inf], np.nan).rdiv(1.0)
    inverse = inverse.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    total = float(inverse.sum())
    if total <= 0:
        return equal_weight(returns)
    return inverse / total


def minimum_variance_weight(
    returns: pd.DataFrame,
    ridge: float = 1e-8,
) -> pd.Series:
    """Estimate long-only minimum-variance weights with a covariance solve."""
    if returns.empty:
        return pd.Series(dtype=float)
    if ridge < 0:
        raise ValueError("ridge must be non-negative")

    columns = list(returns.columns)
    covariance = returns.cov().to_numpy(dtype=float)
    covariance = np.nan_to_num(covariance, nan=0.0)
    covariance += np.eye(len(columns)) * ridge

    try:
        inverse_covariance = np.linalg.pinv(covariance)
        raw = inverse_covariance @ np.ones(len(columns))
    except np.linalg.LinAlgError:
        return equal_weight(returns)

    raw = np.clip(raw, 0.0, None)
    total = float(raw.sum())
    if total <= 0 or not np.isfinite(total):
        return equal_weight(returns)
    return pd.Series(raw / total, index=columns)


def apply_weight_cap(weights: pd.Series, maximum: float) -> pd.Series:
    """Cap individual weights and renormalize the remaining allocation."""
    if maximum <= 0 or maximum > 1:
        raise ValueError("maximum must be between 0 and 1")

    clipped = weights.clip(lower=0.0, upper=maximum)
    if clipped.sum() <= 0:
        return clipped

    for _ in range(len(clipped) + 1):
        excess = float(clipped.sum() - 1.0)
        if excess <= 1e-12:
            break
        free = clipped < maximum - 1e-12
        if not free.any():
            break
        clipped.loc[free] += excess / int(free.sum())
        clipped = clipped.clip(upper=maximum)

    total = float(clipped.sum())
    return clipped / total if total > 0 else clipped


def allocation_summary(weights: pd.Series) -> pd.DataFrame:
    """Return an auditable allocation table."""
    return pd.DataFrame(
        {
            "weight": weights,
            "weight_pct": weights * 100.0,
        }
    )
