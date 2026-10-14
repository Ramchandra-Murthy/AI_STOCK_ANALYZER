"""Validation metrics for comparing theoretical and observed option premiums.

This module consumes caller-supplied observations. It does not fetch market data,
create trading signals, or submit broker orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from collections.abc import Sequence


@dataclass(frozen=True)
class PricingObservation:
    """One paired theoretical and observed premium for a single option contract."""

    observed_price: float
    theoretical_price: float
    option_type: str
    expiry: str
    moneyness: str = "unspecified"
    timestamp: str = ""


@dataclass(frozen=True)
class PricingValidationMetrics:
    """Aggregate model errors; bias is theoretical minus observed price."""

    observation_count: int
    mean_absolute_error: float
    root_mean_squared_error: float
    mean_error_bias: float


def calculate_pricing_validation_metrics(
    observations: Sequence[PricingObservation],
) -> PricingValidationMetrics:
    """Calculate MAE, RMSE and signed bias from validated price pairs.

    Prices must be finite and non-negative. Empty inputs are rejected rather
    than returning misleading zero-error metrics. Duplicate observation keys
    are rejected when timestamp, expiry, option type and moneyness all match.
    """
    if not observations:
        raise ValueError("observations must contain at least one record")

    errors: list[float] = []
    seen: set[tuple[str, str, str, str]] = set()

    for index, observation in enumerate(observations):
        for field_name in ("observed_price", "theoretical_price"):
            value = getattr(observation, field_name)
            if not isfinite(value):
                raise ValueError(f"observation {index}: {field_name} must be finite")
            if value < 0:
                raise ValueError(f"observation {index}: {field_name} must be non-negative")

        option_type = observation.option_type.strip().lower()
        if option_type not in {"call", "put"}:
            raise ValueError(f"observation {index}: option_type must be 'call' or 'put'")
        if not observation.expiry.strip():
            raise ValueError(f"observation {index}: expiry must be non-empty")

        key = (
            observation.timestamp,
            observation.expiry,
            option_type,
            observation.moneyness,
        )
        if observation.timestamp and key in seen:
            raise ValueError(f"observation {index}: duplicate observation key")
        if observation.timestamp:
            seen.add(key)

        errors.append(observation.theoretical_price - observation.observed_price)

    count = len(errors)
    mae = sum(abs(error) for error in errors) / count
    rmse = sqrt(sum(error * error for error in errors) / count)
    bias = sum(errors) / count
    return PricingValidationMetrics(
        observation_count=count,
        mean_absolute_error=mae,
        root_mean_squared_error=rmse,
        mean_error_bias=bias,
    )
