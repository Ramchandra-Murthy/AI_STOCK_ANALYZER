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
from typing import Tuple, Dict, Any, Type, TypeVar, Mapping, Protocol

from services.forecast.exceptions import (
    ForecastValidationError,
    ForecastSerializationError,
)

T = TypeVar("T", bound="Serializable")


class Serializable(Protocol):
    """Protocol defining the serialization contract for all domain models."""

    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls: Type[T], data: Mapping[str, object]) -> T: ...


class ForecastMethod(str, Enum):
    """Supported forecasting calculation algorithms."""

    CAGR = "CAGR"
    LINEAR_REGRESSION = "LINEAR_REGRESSION"
    MEAN_REVERSION = "MEAN_REVERSION"
    ROLLING_AVERAGE = "ROLLING_AVERAGE"
    EXPONENTIAL_SMOOTHING = "EXPONENTIAL_SMOOTHING"
    MANUAL = "MANUAL"


class ConfidenceLevel(str, Enum):
    """Statistical confidence tiers for forecast projections."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ForecastFrequency(str, Enum):
    """Temporal frequency of financial projections."""

    ANNUAL = "ANNUAL"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"


class ScenarioType(str, Enum):
    """Standard multi-scenario classifications."""

    BULL = "BULL"
    BASE = "BASE"
    BEAR = "BEAR"
    CUSTOM = "CUSTOM"


@dataclass(frozen=True, slots=True)
class ForecastMetadata:
    """Immutable audit and provenance metadata for forecasts."""

    created_at: str
    author: str
    version: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls: Type[T], data: Mapping[str, object]) -> T:
        try:
            return cls(
                created_at=str(data["created_at"]),
                author=str(data["author"]),
                version=str(data["version"]),
                description=str(data.get("description", "")),
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ForecastSerializationError(
                f"Failed to deserialize ForecastMetadata: {e}"
            ) from e


@dataclass(frozen=True, slots=True)
class ForecastSeries:
    """Canonical immutable container for numerical time-series projections."""

    values: Tuple[float, ...]
    years: Tuple[int, ...]
    frequency: ForecastFrequency = ForecastFrequency.ANNUAL

    def __post_init__(self) -> None:
        if len(self.values) != len(self.years):
            raise ForecastValidationError(
                f"Length mismatch: values ({len(self.values)}) must match years ({len(self.years)})."
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "values": list(self.values),
            "years": list(self.years),
            "frequency": self.frequency.value,
        }

    @classmethod
    def from_dict(cls: Type[T], data: Mapping[str, object]) -> T:
        try:
            freq_val = data.get("frequency", ForecastFrequency.ANNUAL.value)
            return cls(
                values=tuple(float(v) for v in data["values"]),  # type: ignore
                years=tuple(int(y) for y in data["years"]),  # type: ignore
                frequency=ForecastFrequency(str(freq_val)),
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
    def from_dict(cls: Type[T], data: Mapping[str, object]) -> T:
        try:
            return cls(
                rate=float(data["rate"]),  # type: ignore
                confidence=ConfidenceLevel(str(data["confidence"])),
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
    def from_dict(cls: Type[T], data: Mapping[str, object]) -> T:
        try:
            return cls(
                score=float(data["score"]),  # type: ignore
                level=ConfidenceLevel(str(data["level"])),
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
    def from_dict(cls: Type[T], data: Mapping[str, object]) -> T:
        try:
            return cls(
                revenue_growth_rate=float(data["revenue_growth_rate"]),  # type: ignore
                ebitda_margin=float(data["ebitda_margin"]),  # type: ignore
                tax_rate=float(data["tax_rate"]),  # type: ignore
                capex_pct_revenue=float(data["capex_pct_revenue"]),  # type: ignore
                working_capital_pct_revenue=float(data["working_capital_pct_revenue"]),  # type: ignore
                metadata=dict(data.get("metadata", {})),  # type: ignore
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ForecastSerializationError(
                f"Failed to deserialize ForecastAssumption: {e}"
            ) from e


@dataclass(frozen=True, slots=True)
class ForecastScenario:
    """Canonical container bundling all operational forecasts for a specific scenario."""

    scenario_type: ScenarioType
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
    scenario_name: str = "Base"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_type": self.scenario_type.value,
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
            "scenario_name": self.scenario_name,
        }

    @classmethod
    def from_dict(cls: Type[T], data: Mapping[str, object]) -> T:
        try:
            return cls(
                scenario_type=ScenarioType(str(data["scenario_type"])),
                method=ForecastMethod(str(data["method"])),
                revenue=RevenueForecast.from_dict(data["revenue"]),  # type: ignore
                margins=MarginForecast.from_dict(data["margins"]),  # type: ignore
                capex=CapexForecast.from_dict(data["capex"]),  # type: ignore
                depreciation=DepreciationForecast.from_dict(data["depreciation"]),  # type: ignore
                working_capital=WorkingCapitalForecast.from_dict(data["working_capital"]),  # type: ignore
                taxes=TaxForecast.from_dict(data["taxes"]),  # type: ignore
                terminal_growth=TerminalGrowthForecast.from_dict(data["terminal_growth"]),  # type: ignore
                confidence=ForecastConfidence.from_dict(data["confidence"]),  # type: ignore
                assumptions=ForecastAssumption.from_dict(data["assumptions"]),  # type: ignore
                scenario_name=str(data.get("scenario_name", "Base")),
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ForecastSerializationError(
                f"Failed to deserialize ForecastScenario: {e}"
            ) from e


@dataclass(frozen=True, slots=True)
class ForecastPackage:
    """Canonical multi-scenario package exchanged between downstream valuation engines."""

    ticker: str
    scenarios: Tuple[ForecastScenario, ...]
    metadata: ForecastMetadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "scenarios": [s.to_dict() for s in self.scenarios],
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls: Type[T], data: Mapping[str, object]) -> T:
        try:
            raw_scenarios = data["scenarios"]
            if not isinstance(raw_scenarios, (list, tuple)):
                raise ValueError("Scenarios must be a sequence of dictionaries.")
            scenarios_tuple = tuple(ForecastScenario.from_dict(s) for s in raw_scenarios)  # type: ignore
            metadata_obj = ForecastMetadata.from_dict(data["metadata"])  # type: ignore
            return cls(
                ticker=str(data["ticker"]),
                scenarios=scenarios_tuple,
                metadata=metadata_obj,
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ForecastSerializationError(
                f"Failed to deserialize ForecastPackage: {e}"
            ) from e
