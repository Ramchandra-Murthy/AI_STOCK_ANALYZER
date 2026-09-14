from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, ClassVar

from services.forecast.exceptions import ForecastValidationError


class ForecastMethod(StrEnum):
    CAGR = "CAGR"
    LINEAR_REGRESSION = "LINEAR_REGRESSION"
    ROLLING_AVERAGE = "ROLLING_AVERAGE"
    MANAGEMENT_GUIDANCE = "MANAGEMENT_GUIDANCE"


class ConfidenceLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True, slots=True)
class ForecastLineItem:
    name: str
    values: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "values": list(self.values)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ForecastLineItem:
        return cls(name=data["name"], values=tuple(data["values"]))


@dataclass(frozen=True, slots=True)
class ForecastPackage:
    ticker: str
    years: tuple[int, ...]
    revenue: ForecastLineItem
    net_income: ForecastLineItem
    capex: ForecastLineItem
    depreciation: ForecastLineItem
    working_capital: ForecastLineItem
    tax_rate: ForecastLineItem
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "years": list(self.years),
            "revenue": self.revenue.to_dict(),
            "net_income": self.net_income.to_dict(),
            "capex": self.capex.to_dict(),
            "depreciation": self.depreciation.to_dict(),
            "working_capital": self.working_capital.to_dict(),
            "tax_rate": self.tax_rate.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ForecastPackage:
        return cls(
            ticker=data["ticker"],
            years=tuple(data["years"]),
            revenue=ForecastLineItem.from_dict(data["revenue"]),
            net_income=ForecastLineItem.from_dict(data["net_income"]),
            capex=ForecastLineItem.from_dict(data["capex"]),
            depreciation=ForecastLineItem.from_dict(data["depreciation"]),
            working_capital=ForecastLineItem.from_dict(data["working_capital"]),
            tax_rate=ForecastLineItem.from_dict(data["tax_rate"]),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True, slots=True)
class _ForecastSeries:
    values: tuple[float, ...]
    years: tuple[int, ...]
    _kind: ClassVar[str] = "forecast"

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", tuple(float(value) for value in self.values))
        object.__setattr__(self, "years", tuple(int(year) for year in self.years))
        if len(self.values) != len(self.years):
            raise ForecastValidationError("values and years must have the same length")

    def to_dict(self) -> dict[str, Any]:
        return {"values": list(self.values), "years": list(self.years)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> _ForecastSeries:
        return cls(values=tuple(data["values"]), years=tuple(data["years"]))


@dataclass(frozen=True, slots=True)
class RevenueForecast(_ForecastSeries):
    pass


@dataclass(frozen=True, slots=True)
class MarginForecast(_ForecastSeries):
    def __post_init__(self) -> None:
        super(MarginForecast, self).__post_init__()
        if any(value < 0.0 or value > 1.0 for value in self.values):
            raise ForecastValidationError("margin values must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class CapexForecast(_ForecastSeries):
    pass


@dataclass(frozen=True, slots=True)
class DepreciationForecast(_ForecastSeries):
    pass


@dataclass(frozen=True, slots=True)
class WorkingCapitalForecast(_ForecastSeries):
    pass


@dataclass(frozen=True, slots=True)
class TaxForecast(_ForecastSeries):
    pass


@dataclass(frozen=True, slots=True)
class TerminalGrowthForecast:
    rate: float
    confidence: ConfidenceLevel

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", ConfidenceLevel(self.confidence))
        if not 0.0 <= self.rate < 1.0:
            raise ForecastValidationError("terminal growth rate must be in [0, 1)")

    def to_dict(self) -> dict[str, Any]:
        return {"rate": self.rate, "confidence": self.confidence.value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TerminalGrowthForecast:
        return cls(rate=float(data["rate"]), confidence=ConfidenceLevel(data["confidence"]))


@dataclass(frozen=True, slots=True)
class ForecastConfidence:
    score: float
    level: ConfidenceLevel

    def __post_init__(self) -> None:
        object.__setattr__(self, "level", ConfidenceLevel(self.level))
        if not 0.0 <= self.score <= 100.0:
            raise ForecastValidationError("confidence score must be between 0 and 100")

    def to_dict(self) -> dict[str, Any]:
        return {"score": self.score, "level": self.level.value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ForecastConfidence:
        return cls(score=float(data["score"]), level=ConfidenceLevel(data["level"]))


@dataclass(frozen=True, slots=True)
class ForecastAssumption:
    revenue_growth_rate: float
    ebitda_margin: float
    tax_rate: float
    capex_pct_revenue: float
    working_capital_pct_revenue: float

    def to_dict(self) -> dict[str, float]:
        return {
            "revenue_growth_rate": self.revenue_growth_rate,
            "ebitda_margin": self.ebitda_margin,
            "tax_rate": self.tax_rate,
            "capex_pct_revenue": self.capex_pct_revenue,
            "working_capital_pct_revenue": self.working_capital_pct_revenue,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ForecastAssumption:
        return cls(
            **{
                key: float(data[key])
                for key in (
                    "revenue_growth_rate",
                    "ebitda_margin",
                    "tax_rate",
                    "capex_pct_revenue",
                    "working_capital_pct_revenue",
                )
            }
        )


@dataclass(frozen=True, slots=True)
class ForecastScenario:
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

    def __post_init__(self) -> None:
        object.__setattr__(self, "method", ForecastMethod(self.method))

    def to_dict(self) -> dict[str, Any]:
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
    def from_dict(cls, data: dict[str, Any]) -> ForecastScenario:
        return cls(
            scenario_name=data["scenario_name"],
            method=ForecastMethod(data["method"]),
            revenue=RevenueForecast.from_dict(data["revenue"]),
            margins=MarginForecast.from_dict(data["margins"]),
            capex=CapexForecast.from_dict(data["capex"]),
            depreciation=DepreciationForecast.from_dict(data["depreciation"]),
            working_capital=WorkingCapitalForecast.from_dict(data["working_capital"]),
            taxes=TaxForecast.from_dict(data["taxes"]),
            terminal_growth=TerminalGrowthForecast.from_dict(data["terminal_growth"]),
            confidence=ForecastConfidence.from_dict(data["confidence"]),
            assumptions=ForecastAssumption.from_dict(data["assumptions"]),
        )
