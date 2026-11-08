"""Fit the square-root market-impact model to observed execution shortfall."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MarketImpactCalibration:
    """Fitted impact parameters and in-sample goodness-of-fit diagnostics."""

    impact_coefficient: float
    half_spread_bps: float
    observations: int
    rmse_bps: float
    r_squared: float | None


def calibrate_market_impact(
    observed_shortfall_bps: pd.Series,
    participation_rate: pd.Series,
    volatility: pd.Series,
) -> MarketImpactCalibration:
    """Fit non-negative spread and square-root impact parameters by least squares.

    The fitted model is:
        shortfall_bps = half_spread_bps
            + impact_coefficient * volatility * sqrt(participation_rate) * 10000

    Inputs must represent comparable one-way execution shortfall observations.
    This estimates a research-model fit; it does not guarantee future execution.
    """
    series = (observed_shortfall_bps, participation_rate, volatility)
    if any(not values.index.is_unique for values in series):
        raise ValueError("calibration inputs must not contain duplicate indexes")
    index = observed_shortfall_bps.index
    if any(not index.equals(values.index) for values in series[1:]):
        raise ValueError("calibration inputs must have identical indexes")
    if len(index) < 3:
        raise ValueError("at least three calibration observations are required")

    data = pd.DataFrame(
        {
            "shortfall": pd.to_numeric(observed_shortfall_bps, errors="coerce"),
            "participation": pd.to_numeric(participation_rate, errors="coerce"),
            "volatility": pd.to_numeric(volatility, errors="coerce"),
        },
        index=index,
    )
    values = data.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("calibration inputs must contain only finite numeric values")
    if (data["shortfall"] < 0).any():
        raise ValueError("observed shortfall must be non-negative")
    if ((data["participation"] <= 0) | (data["participation"] > 1)).any():
        raise ValueError("participation_rate must be in (0, 1]")
    if (data["volatility"] < 0).any():
        raise ValueError("volatility must be non-negative")

    feature = (
        data["volatility"].to_numpy(dtype=float)
        * np.sqrt(data["participation"].to_numpy(dtype=float))
        * 10_000.0
    )
    if np.ptp(feature) <= np.finfo(float).eps:
        raise ValueError("calibration requires variation in volatility-adjusted participation")

    target = data["shortfall"].to_numpy(dtype=float)
    design = np.column_stack((np.ones(len(feature)), feature))
    candidates: list[tuple[float, float]] = []

    unconstrained, *_ = np.linalg.lstsq(design, target, rcond=None)
    if (unconstrained >= 0).all():
        candidates.append((float(unconstrained[0]), float(unconstrained[1])))

    intercept_only = max(float(target.mean()), 0.0)
    candidates.append((intercept_only, 0.0))

    slope_only = max(float(np.dot(feature, target) / np.dot(feature, feature)), 0.0)
    candidates.append((0.0, slope_only))
    candidates.append((0.0, 0.0))

    half_spread, coefficient = min(
        candidates,
        key=lambda pair: float(np.square(target - (pair[0] + pair[1] * feature)).sum()),
    )
    predicted = half_spread + coefficient * feature
    residual = target - predicted
    rmse = float(np.sqrt(np.mean(np.square(residual))))
    total_variance = float(np.square(target - target.mean()).sum())
    r_squared = (
        float(1.0 - np.square(residual).sum() / total_variance) if total_variance > 0 else None
    )
    return MarketImpactCalibration(
        impact_coefficient=coefficient,
        half_spread_bps=half_spread,
        observations=len(target),
        rmse_bps=rmse,
        r_squared=r_squared,
    )
