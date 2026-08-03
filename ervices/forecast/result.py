"""
==========================================================
FORECAST ENGINE RESULT DOMAIN CONTRACTS
Module  : services.forecast.result
Layer   : Services / Forecast / Output DTOs
==========================================================

Purpose
-------
Defines immutable output data structures and summary wrappers
returned by the Forecast Engine upon successful execution.

Dependencies
------------
Standard Library only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from services.forecast.models import (
    ConfidenceLevel,
    ForecastMethod,
    MarginForecast,
    RevenueForecast,
)


@dataclass(frozen=True, slots=True)
class ForecastResult:
    """
    Immutable aggregate result payload returned by the Forecast Engine.
    Encapsulates all projected line items, applied metadata, and confidence metrics.
    """

    symbol: str
    forecast_horizon: int
    method_used: ForecastMethod
    confidence_level: ConfidenceLevel
    confidence_score: float
    revenue_forecast: RevenueForecast
    margin_forecast: MarginForecast
    ebit_forecast: Tuple[float, ...] = field(default_factory=tuple)
    nwc_forecast: Tuple[float, ...] = field(default_factory=tuple)
    capex_forecast: Tuple[float, ...] = field(default_factory=tuple)
    depreciation_forecast: Tuple[float, ...] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the complete forecast result payload to a standard dictionary."""
        return {
            "symbol": self.symbol,
            "forecast_horizon": self.forecast_horizon,
            "method_used": self.method_used.value,
            "confidence_level": self.confidence_level.value,
            "confidence_score": self.confidence_score,
            "revenue_forecast": self.revenue_forecast.to_dict(),
            "margin_forecast": self.margin_forecast.to_dict(),
            "ebit_forecast": list(self.ebit_forecast),
            "nwc_forecast": list(self.nwc_forecast),
            "capex_forecast": list(self.capex_forecast),
            "depreciation_forecast": list(self.depreciation_forecast),
            "metadata": self.metadata,
        }
