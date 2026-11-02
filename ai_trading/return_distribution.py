"""Book-aligned return-distribution diagnostics for strategy results."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _clean_returns(returns: pd.Series) -> pd.Series:
    """Coerce returns to numeric, ignore missing values, and reject infinities."""
    clean = pd.to_numeric(returns, errors="coerce").dropna()
    if not np.isfinite(clean.to_numpy(dtype=float)).all():
        raise ValueError("returns must contain only finite numeric values")
    return clean


def return_distribution_summary(returns: pd.Series) -> dict[str, float | None]:
    """Summarize skewness, kurtosis, and tail behavior of returns."""
    clean = _clean_returns(returns)
    if clean.empty:
        return {
            "observations": 0.0,
            "mean": None,
            "std": None,
            "skewness": None,
            "kurtosis": None,
            "positive_fraction": None,
            "negative_fraction": None,
        }

    return {
        "observations": float(len(clean)),
        "mean": float(clean.mean()),
        "std": float(clean.std(ddof=1)) if len(clean) > 1 else 0.0,
        "skewness": float(clean.skew()) if len(clean) > 2 else 0.0,
        "kurtosis": float(clean.kurt()) if len(clean) > 3 else 0.0,
        "positive_fraction": float((clean > 0.0).mean()),
        "negative_fraction": float((clean < 0.0).mean()),
    }


def downside_deviation(
    returns: pd.Series,
    *,
    target: float = 0.0,
) -> float:
    """Return the downside deviation below a finite numeric target return."""
    if isinstance(target, (bool, np.bool_)):
        raise ValueError("target must be a finite numeric value")
    try:
        target_value = float(target)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("target must be a finite numeric value") from exc
    if not math.isfinite(target_value):
        raise ValueError("target must be a finite numeric value")

    clean = _clean_returns(returns)
    if clean.empty:
        return 0.0

    downside = (clean - target_value).clip(upper=0.0)
    return float(math.sqrt((downside.pow(2)).mean()))
