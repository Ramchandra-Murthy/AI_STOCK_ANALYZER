"""Deterministic bootstrap uncertainty intervals for market-impact calibration."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from algorithmic_trading.impact_calibration import (
    MarketImpactCalibration,
    calibrate_market_impact,
)


@dataclass(frozen=True)
class MarketImpactBootstrap:
    """Point estimates and percentile intervals for fitted impact parameters."""

    calibration: MarketImpactCalibration
    confidence: float
    requested_samples: int
    successful_samples: int
    half_spread_lower_bps: float
    half_spread_upper_bps: float
    impact_coefficient_lower: float
    impact_coefficient_upper: float


def bootstrap_market_impact_calibration(
    observed_shortfall_bps: pd.Series,
    participation_rate: pd.Series,
    volatility: pd.Series,
    *,
    samples: int = 1000,
    confidence: float = 0.95,
    seed: int = 42,
) -> MarketImpactBootstrap:
    """Estimate percentile-bootstrap intervals by resampling aligned observations.

    Each bootstrap replicate resamples complete observation triplets, preserving
    the pairing between realized shortfall, participation and volatility. The
    original sample is fitted once for point estimates. Replicates that cannot
    identify the model because their predictor has no variation are discarded.
    At least 80% of requested replicates must produce valid fits.
    """
    if samples < 1:
        raise ValueError("samples must be at least 1")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")

    calibration = calibrate_market_impact(
        observed_shortfall_bps,
        participation_rate,
        volatility,
    )
    count = calibration.observations
    target = observed_shortfall_bps.to_numpy(dtype=float)
    participation = participation_rate.to_numpy(dtype=float)
    volatility_values = volatility.to_numpy(dtype=float)
    rng = np.random.default_rng(seed)

    half_spreads: list[float] = []
    coefficients: list[float] = []
    for _ in range(samples):
        indices = rng.integers(0, count, size=count)
        try:
            fitted = calibrate_market_impact(
                pd.Series(target[indices]),
                pd.Series(participation[indices]),
                pd.Series(volatility_values[indices]),
            )
        except ValueError as exc:
            if "variation in volatility-adjusted participation" not in str(exc):
                raise
            continue
        half_spreads.append(fitted.half_spread_bps)
        coefficients.append(fitted.impact_coefficient)

    successful = len(coefficients)
    minimum_successful = int(np.ceil(samples * 0.8))
    if successful < minimum_successful:
        raise ValueError("insufficient valid bootstrap samples; predictor variation is too limited")

    tail = (1.0 - confidence) / 2.0
    lower, upper = tail, 1.0 - tail
    spread_interval = np.quantile(half_spreads, [lower, upper])
    coefficient_interval = np.quantile(coefficients, [lower, upper])

    return MarketImpactBootstrap(
        calibration=calibration,
        confidence=confidence,
        requested_samples=samples,
        successful_samples=successful,
        half_spread_lower_bps=float(spread_interval[0]),
        half_spread_upper_bps=float(spread_interval[1]),
        impact_coefficient_lower=float(coefficient_interval[0]),
        impact_coefficient_upper=float(coefficient_interval[1]),
    )
