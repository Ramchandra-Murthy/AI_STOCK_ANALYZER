"""Compatibility exports for the legacy forecast API.

Older forecast subservices import their shared input and enum contracts from
this module. Keep the compatibility definitions here while the newer forecast
package remains the implementation used by current callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from services.forecast.models import ForecastMethod


class ScenarioType(str, Enum):
    BASE = "BASE"
    BULL = "BULL"
    BEAR = "BEAR"


@dataclass(frozen=True, slots=True)
class AlgorithmInput:
    """Normalized input passed to legacy forecasting algorithms."""

    historical_values: tuple[float, ...]
    forecast_periods: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "historical_values", tuple(float(value) for value in self.historical_values)
        )
        if self.forecast_periods < 1:
            raise ValueError("forecast_periods must be at least 1")


__all__ = ["AlgorithmInput", "ForecastMethod", "ScenarioType"]
