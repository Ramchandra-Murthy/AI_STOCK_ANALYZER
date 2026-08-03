"""
==========================================================
FORECAST DOMAIN MODELS MODULE
Module  : services.forecast.models
Layer   : Services / Forecast / Domain Models
==========================================================

Purpose
-------
Defines immutable domain models, value objects, and enumerations
used across the institutional financial forecasting pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Tuple


class ForecastMethod(str, Enum):
    """Enumeration of available quantitative forecasting methodologies."""

    CAGR = "cagr"
    HISTORICAL_MEAN = "historical_mean"
    LINEAR_REGRESSION = "linear_regression"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    MANAGEMENT_GUIDANCE = "management_guidance"
    MANUAL = "manual"


class ConfidenceLevel(str, Enum):
    """Qualitative confidence levels for forecast projections."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(slots=True, frozen=True)
class ForecastAssumption:
    """Immutable value object capturing specific baseline assumptions."""

    parameter_name: str
    value: float
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        """Serializes assumption attributes into a standard dictionary."""
        return {
            "parameter_name": self.parameter_name,
            "value": self.value,
            "rationale": self.rationale,
        }


@dataclass(slots=True, frozen=True)
class ForecastSeries:
    """Immutable generic container for historical and projected time-series data."""

    historical: Tuple[float, ...]
    projected: Tuple[float, ...]
    method: ForecastMethod
    confidence: ConfidenceLevel

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the time series payload to a standard dictionary."""
        return {
            "historical": list(self.historical),
            "projected": list(self.projected),
            "method": self.method.value,
            "confidence": self.confidence.value,
        }


@dataclass(slots=True, frozen=True)
class RevenueForecast:
    """Immutable value object containing revenue projections and metadata."""

    historical: Tuple[float, ...]
    projected: Tuple[float, ...]
    method: ForecastMethod
    confidence: ConfidenceLevel
    growth_rates: Tuple[float, ...] = field(default_factory=tuple)
    projected_revenue: Tuple[float, ...] = field(default_factory=tuple)
    guidance_override_applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the revenue forecast payload to a standard dictionary."""
        return {
            "historical": list(self.historical),
            "projected": list(self.projected),
            "method": self.method.value,
            "confidence": self.confidence.value,
            "growth_rates": list(self.growth_rates),
            "projected_revenue": list(self.projected_revenue),
            "guidance_override_applied": self.guidance_override_applied,
        }


@dataclass(slots=True, frozen=True)
class MarginForecast:
    """Immutable value object containing profitability margin projections."""

    historical: Tuple[float, ...]
    projected: Tuple[float, ...]
    method: ForecastMethod
    confidence: ConfidenceLevel
    margins: Tuple[float, ...] = field(default_factory=tuple)
    metric_name: str = "ebit_margin"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the margin forecast payload to a standard dictionary."""
        return {
            "historical": list(self.historical),
            "projected": list(self.projected),
            "method": self.method.value,
            "confidence": self.confidence.value,
            "margins": list(self.margins),
            "metric_name": self.metric_name,
        }


@dataclass(slots=True, frozen=True)
class CapexForecast:
    """Immutable value object containing capital expenditure projections."""

    historical: Tuple[float, ...]
    projected: Tuple[float, ...]
    method: ForecastMethod
    confidence: ConfidenceLevel
    capex_ratio: float = 0.05
    capex: Tuple[float, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the capex forecast payload to a standard dictionary."""
        return {
            "historical": list(self.historical),
            "projected": list(self.projected),
            "method": self.method.value,
            "confidence": self.confidence.value,
            "capex_ratio": self.capex_ratio,
            "capex": list(self.capex),
        }


@dataclass(slots=True, frozen=True)
class DepreciationForecast:
    """Immutable value object containing depreciation and amortization projections."""

    historical: Tuple[float, ...]
    projected: Tuple[float, ...]
    method: ForecastMethod
    confidence: ConfidenceLevel
    depreciation_rate: float = 0.04
    depreciation: Tuple[float, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the depreciation forecast payload to a standard dictionary."""
        return {
            "historical": list(self.historical),
            "projected": list(self.projected),
            "method": self.method.value,
            "confidence": self.confidence.value,
            "depreciation_rate": self.depreciation_rate,
            "depreciation": list(self.depreciation),
        }


@dataclass(slots=True, frozen=True)
class WorkingCapitalForecast:
    """Immutable value object containing working capital projections."""

    historical: Tuple[float, ...]
    projected: Tuple[float, ...]
    method: ForecastMethod
    confidence: ConfidenceLevel
    nwc_percentage_of_revenue: float = 0.15
    working_capital: Tuple[float, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the working capital forecast payload to a standard dictionary."""
        return {
            "historical": list(self.historical),
            "projected": list(self.projected),
            "method": self.method.value,
            "confidence": self.confidence.value,
            "nwc_percentage_of_revenue": self.nwc_percentage_of_revenue,
            "working_capital": list(self.working_capital),
        }


@dataclass(slots=True, frozen=True)
class TaxForecast:
    """Immutable value object containing tax liability projections."""

    historical: Tuple[float, ...]
    projected: Tuple[float, ...]
    method: ForecastMethod
    confidence: ConfidenceLevel
    effective_tax_rate: float = 0.25
    tax_liabilities: Tuple[float, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the tax forecast payload to a standard dictionary."""
        return {
            "historical": list(self.historical),
            "projected": list(self.projected),
            "method": self.method.value,
            "confidence": self.confidence.value,
            "effective_tax_rate": self.effective_tax_rate,
            "tax_liabilities": list(self.tax_liabilities),
        }


@dataclass(slots=True, frozen=True)
class TerminalGrowthForecast:
    """Immutable value object containing terminal growth rate projections."""

    historical_gdp_growth: Tuple[float, ...]
    terminal_growth_rate: float
    method: ForecastMethod
    confidence: ConfidenceLevel

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the terminal growth forecast payload to a standard dictionary."""
        return {
            "historical_gdp_growth": list(self.historical_gdp_growth),
            "terminal_growth_rate": self.terminal_growth_rate,
            "method": self.method.value,
            "confidence": self.confidence.value,
        }


@dataclass(slots=True, frozen=True)
class ForecastConfidence:
    """Immutable value object measuring overall model confidence scores."""

    overall_score: float
    qualitative_rating: ConfidenceLevel
    component_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the confidence score payload to a standard dictionary."""
        return {
            "overall_score": self.overall_score,
            "qualitative_rating": self.qualitative_rating.value,
            "component_scores": self.component_scores,
        }


@dataclass(slots=True, frozen=True)
class ForecastScenario:
    """Immutable container representing a full financial scenario configuration."""

    scenario_name: str
    method: ForecastMethod
    probability: float = 1.0
    assumptions: Tuple[ForecastAssumption, ...] = field(default_factory=tuple)
    overrides: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the full scenario definition to a standard dictionary."""
        return {
            "scenario_name": self.scenario_name,
            "method": self.method.value,
            "probability": self.probability,
            "assumptions": [a.to_dict() for a in self.assumptions],
            "overrides": self.overrides,
        }


@dataclass(slots=True, frozen=True)
class HistoricalFinancials:
    """Immutable container for historical financial statement items."""

    revenue: Tuple[float, ...]
    ebitda: Tuple[float, ...] = field(default_factory=tuple)
    ebit: Tuple[float, ...] = field(default_factory=tuple)
    net_income: Tuple[float, ...] = field(default_factory=tuple)
    capex: Tuple[float, ...] = field(default_factory=tuple)
    depreciation: Tuple[float, ...] = field(default_factory=tuple)
    working_capital: Tuple[float, ...] = field(default_factory=tuple)
    nwc: Tuple[float, ...] = field(default_factory=tuple)


@dataclass(slots=True, frozen=True)
class ScenarioOverrides:
    """Immutable container for scenario-specific override configurations."""

    revenue_growth_override: Optional[float] = None
    margin_override: Optional[float] = None
    capex_ratio_override: Optional[float] = None
