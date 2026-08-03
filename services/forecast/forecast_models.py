"""
==========================================================
FORECAST DOMAIN MODELS

Module  : forecast_models
Version : 5.1.0
Layer   : Forecast Domain
==========================================================

Purpose
-------
Defines immutable domain models for the Forecast Engine using pure
dataclasses, strict typing, and protocol contracts.

Dependencies
------------
Standard Library only.

Public API
----------
ForecastMethod
ConfidenceLevel
ForecastProtocol
ForecastSeries
RevenueForecast
MarginForecast
CapexForecast
DepreciationForecast
WorkingCapitalForecast
TaxForecast
TerminalGrowthForecast
ForecastScenario
ForecastConfidence
ForecastAssumption
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Protocol, Tuple, runtime_checkable


class ForecastMethod(str, Enum):
    """Supported mathematical calculation methodologies for projections."""

    CAGR = "cagr"
    HISTORICAL_MEAN = "historical_mean"
    LINEAR_REGRESSION = "linear_regression"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    MANAGEMENT_GUIDANCE = "management_guidance"


class ConfidenceLevel(str, Enum):
    """Qualitative confidence tiers assigned to forecast outputs."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


@runtime_checkable
class ForecastProtocol(Protocol):
    """Structural protocol defining common attributes for all forecast series objects."""

    historical: Tuple[float, ...]
    projected: Tuple[float, ...]
    method: ForecastMethod
    confidence: ConfidenceLevel

    def to_dict(self) -> Dict[str, Any]:
        """Serializes forecast series to dictionary format."""
        ...


@dataclass(frozen=True, slots=True)
class ForecastAssumption:
    """Immutable representation of a foundational forecast assumption."""

    name: str
    value: float
    description: str
    source: str = "historical_analysis"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes assumption to standard dictionary format."""
        return {
            "name": self.name,
            "value": self.value,
            "description": self.description,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class ForecastConfidence:
    """Quantitative scoring structure measuring projection reliability."""

    confidence_score: float
    confidence_level: ConfidenceLevel
    volatility_score: float
    data_quality_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Serializes confidence metrics to dictionary format."""
        return {
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level.value,
            "volatility_score": self.volatility_score,
            "data_quality_score": self.data_quality_score,
        }


@dataclass(frozen=True, slots=True)
class ForecastSeries:
    """Generic immutable base model for financial time-series projections."""

    historical: Tuple[float, ...] = field(default_factory=tuple)
    projected: Tuple[float, ...] = field(default_factory=tuple)
    method: ForecastMethod = ForecastMethod.HISTORICAL_MEAN
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    assumptions: Tuple[ForecastAssumption, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes base series data structure to dictionary format."""
        return {
            "historical": list(self.historical),
            "projected": list(self.projected),
            "method": self.method.value,
            "confidence": self.confidence.value,
            "assumptions": [a.to_dict() for a in self.assumptions],
        }


@dataclass(frozen=True, slots=True)
class RevenueForecast(ForecastSeries):
    """Immutable value object containing projected revenue series and growth rates."""

    growth_rates: Tuple[float, ...] = field(default_factory=tuple)
    projected_revenue: Tuple[float, ...] = field(default_factory=tuple)
    guidance_override_applied: bool = False

    def __post_init__(self) -> None:
        if not self.projected and self.projected_revenue:
            object.__setattr__(self, "projected", self.projected_revenue)
        elif not self.projected_revenue and self.projected:
            object.__setattr__(self, "projected_revenue", self.projected)


@dataclass(frozen=True, slots=True)
class MarginForecast(ForecastSeries):
    """Immutable value object capturing projected margins (e.g., EBITDA)."""

    margins: Tuple[float, ...] = field(default_factory=tuple)
    projected_margins: Tuple[float, ...] = field(default_factory=tuple)
    metric_name: str = "ebitda_margin"

    def __post_init__(self) -> None:
        if not self.margins and self.projected_margins:
            object.__setattr__(self, "margins", self.projected_margins)
        elif not self.projected_margins and self.margins:
            object.__setattr__(self, "projected_margins", self.margins)


@dataclass(frozen=True, slots=True)
class CapexForecast(ForecastSeries):
    """Immutable capital expenditures forecast structure."""

    projected_capex: Tuple[float, ...] = field(default_factory=tuple)
    capex_as_pct_revenue: Tuple[float, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class DepreciationForecast(ForecastSeries):
    """Immutable depreciation and amortization forecast structure."""

    projected_depreciation: Tuple[float, ...] = field(default_factory=tuple)
    depr_as_pct_capex: Tuple[float, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class WorkingCapitalForecast(ForecastSeries):
    """Immutable net working capital (NWC) forecast structure."""

    projected_nwc: Tuple[float, ...] = field(default_factory=tuple)
    nwc_change: Tuple[float, ...] = field(default_factory=tuple)
    nwc_as_pct_revenue: Tuple[float, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class TaxForecast(ForecastSeries):
    """Immutable tax expense and effective tax rate forecast."""

    projected_tax_rate: Tuple[float, ...] = field(default_factory=tuple)
    projected_tax_expense: Tuple[float, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class TerminalGrowthForecast:
    """Immutable terminal value and perpetuity growth assumptions."""

    terminal_growth_rate: float
    perpetuity_growth_rate: float
    method_rationale: str = "Standard macroeconomic normalization"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes terminal growth contract to dictionary format."""
        return {
            "terminal_growth_rate": self.terminal_growth_rate,
            "perpetuity_growth_rate": self.perpetuity_growth_rate,
            "method_rationale": self.method_rationale,
        }


@dataclass(frozen=True, slots=True)
class ForecastScenario:
    """Immutable multi-scenario modeling parameters."""

    scenario_name: str
    probability: float
    revenue_multiplier: float
    margin_expansion_bps: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serializes scenario parameters to dictionary format."""
        return {
            "scenario_name": self.scenario_name,
            "probability": self.probability,
            "revenue_multiplier": self.revenue_multiplier,
            "margin_expansion_bps": self.margin_expansion_bps,
        }
