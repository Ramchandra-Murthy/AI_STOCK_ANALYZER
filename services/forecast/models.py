"""
==========================================================
CANONICAL FORECAST DOMAIN MODELS
Module  : services.forecast.models
Layer   : Forecast Domain
==========================================================
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Tuple, Dict, Any, Type, TypeVar

from services.forecast.exceptions import (
    ForecastValidationError,
    ForecastSerializationError,
)

T = TypeVar("T", bound="BaseModel")


class ForecastMethod(str, Enum):
    """Supported forecasting calculation algorithms."""

    CAGR = "CAGR"
    LINEAR_REGRESSION = "LINEAR_REGRESSION"
    MEAN_REVERSION = "MEAN_REVERSION"
    ROLLING_AVERAGE = "ROLLING_AVERAGE"
    MANUAL = "MANUAL"


class ConfidenceLevel(str, Enum):
    """Statistical confidence tiers for forecast projections."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True, slots=True)
class ForecastSeries:
    """Canonical immutable container for numerical time-series projections."""

    values: Tuple[float, ...]
    years: Tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.values) != len(self.years):
            raise ForecastValidationError(
                f"Length mismatch: values ({len(self.values)}) must match years ({len(self.years)})."
            )

    def to_dict(self) -> Dict[str, Any]:
        return {"values": list(self.values), "years": list(self.years)}

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        try:
            return cls(
                values=tuple(float(v) for v in data["values"]),
                years=tuple(int(y) for y in data["years"]),
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ForecastSerializationError(
                f"Failed to deserialize ForecastSeries: {e}"
            ) from e


@dataclass(frozen=True, slots=True)
class RevenueForecast(ForecastSeries):
    """Specialized immutable series container for Revenue projections."""

    pass


@dataclass(frozen=True, slots=True)
class MarginForecast(ForecastSeries):
    """Specialized immutable series container for Operating/EBITDA Margins."""

    def __post_init__(self) -> None:
        super().__post_init__()
        for val in self.values:
            if not (0.0 <= val <= 1.0):
                raise ForecastValidationError(
                    f"Margin value {val} must be between 0.0 and 1.0."
                )


@dataclass(frozen=True, slots=True)
class CapexForecast(ForecastSeries):
    """Specialized immutable series container for Capital Expenditures."""

    pass


@dataclass(frozen=True, slots=True)
class DepreciationForecast(ForecastSeries):
    """Specialized immutable series container for Depreciation & Amortization."""

    pass


@dataclass(frozen=True, slots=True)
class WorkingCapitalForecast(ForecastSeries):
    """Specialized immutable series container for Working Capital metrics."""

    pass


@dataclass(frozen=True, slots=True)
class TaxForecast(ForecastSeries):
    """Specialized immutable series container for Effective Tax Rates."""

    def __post_init__(self) -> None:
        super().__post_init__()
        for val in self.values:
            if not (0.0 <= val <= 1.0):
                raise ForecastValidationError(
                    f"Tax rate value {val} must be between 0.0 and 1.0."
                )


@dataclass(frozen=True, slots=True)
class TerminalGrowthForecast:
    """Immutable model representing terminal growth assumptions."""

    rate: float
    confidence: ConfidenceLevel

    def __post_init__(self) -> None:
        if not (-0.05 <= self.rate <= 0.10):
            raise ForecastValidationError(
                f"Terminal growth rate {self.rate} outside valid bounds [-5%, 10%]."
            )

    def to_dict(self) -> Dict[str, Any]:
        return {"rate": self.rate, "confidence": self.confidence.value}

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        try:
            return cls(
                rate=float(data["rate"]),
                confidence=ConfidenceLevel(data["confidence"]),
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ForecastSerializationError(
                f"Failed to deserialize TerminalGrowthForecast: {e}"
            ) from e


@dataclass(frozen=True, slots=True)
class ForecastConfidence:
    """Immutable confidence metadata container."""

    score: float  # 0.0 to 100.0
    level: ConfidenceLevel

    def __post_init__(self) -> None:
        if not (0.0 <= self.score <= 100.0):
            raise ForecastValidationError(
                f"Confidence score {self.score} must be between 0.0 and 100.0."
            )

    def to_dict(self) -> Dict[str, Any]:
        return {"score": self.score, "level": self.level.value}

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        try:
            return cls(
                score=float(data["score"]),
                level=ConfidenceLevel(data["level"]),
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ForecastSerializationError(
                f"Failed to deserialize ForecastConfidence: {e}"
            ) from e


@dataclass(frozen=True, slots=True)
class ForecastAssumption:
    """Immutable operational assumptions governing forward projections."""

    revenue_growth_rate: float
    ebitda_margin: float
    tax_rate: float
    capex_pct_revenue: float
    working_capital_pct_revenue: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (-1.0 <= self.revenue_growth_rate <= 5.0):
            raise ForecastValidationError(
                f"Revenue growth rate {self.revenue_growth_rate} out of bounds."
            )
        if not (0.0 <= self.ebitda_margin <= 1.0):
            raise ForecastValidationError(
                f"EBITDA margin {self.ebitda_margin} must be between 0.0 and 1.0."
            )
        if not (0.0 <= self.tax_rate <= 1.0):
            raise ForecastValidationError(
                f"Tax rate {self.tax_rate} must be between 0.0 and 1.0."
            )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        try:
            return cls(
                revenue_growth_rate=float(data["revenue_growth_rate"]),
                ebitda_margin=float(data["ebitda_margin"]),
                tax_rate=float(data["tax_rate"]),
                capex_pct_revenue=float(data["capex_pct_revenue"]),
                working_capital_pct_revenue=float(data["working_capital_pct_revenue"]),
                metadata=dict(data.get("metadata", {})),
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ForecastSerializationError(
                f"Failed to deserialize ForecastAssumption: {e}"
            ) from e


@dataclass(frozen=True, slots=True)
class ForecastScenario:
    """Canonical multi-statement container bundling all operational forecasts."""

    scenario_name: str
    method: ForecastMethod
    revenue: RevenueForecast
    margins: MarginForecast
    capex: CapexForecast
    depreciation: DepreciationForecast
    working_capital: WorkingCapitalForecast
    taxes: TaxForecast
    terminal_growth: TerminalGrowthForecast
    confidence: ForecastConfidence
    assumptions: ForecastAssumption

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "method": self.method.value,
            "revenue": self.revenue.to_dict(),
            "margins": self.margins.to_dict(),
            "capex": self.capex.to_dict(),
            "depreciation": self.depreciation.to_dict(),
            "working_capital": self.working_capital.to_dict(),
            "taxes": self.taxes.to_dict(),
            "terminal_growth": self.terminal_growth.to_dict(),
            "confidence": self.confidence.to_dict(),
            "assumptions": self.assumptions.to_dict(),
        }

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        try:
            return cls(
                scenario_name=str(data["scenario_name"]),
                method=ForecastMethod(data["method"]),
                revenue=RevenueForecast.from_dict(data["revenue"]),
                margins=MarginForecast.from_dict(data["margins"]),
                capex=CapexForecast.from_dict(data["capex"]),
                depreciation=DepreciationForecast.from_dict(data["depreciation"]),
                working_capital=WorkingCapitalForecast.from_dict(
                    data["working_capital"]
                ),
                taxes=TaxForecast.from_dict(data["taxes"]),
                terminal_growth=TerminalGrowthForecast.from_dict(
                    data["terminal_growth"]
                ),
                confidence=ForecastConfidence.from_dict(data["confidence"]),
                assumptions=ForecastAssumption.from_dict(data["assumptions"]),
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ForecastSerializationError(
                f"Failed to deserialize ForecastScenario: {e}"
            ) from e
