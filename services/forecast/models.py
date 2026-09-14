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
    HISTORICAL_MEAN = "HISTORICAL_MEAN"


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


@dataclass(frozen=True, slots=True, init=False)
class _ForecastSeries:
    values: tuple[float, ...]
    years: tuple[int, ...]
    historical: tuple[float, ...]
    projected: tuple[float, ...]
    method: ForecastMethod
    confidence: ConfidenceLevel
    growth_rates: tuple[float, ...]
    _kind: ClassVar[str] = "forecast"

    def __init__(
        self,
        values: tuple[float, ...] = (),
        years: tuple[int, ...] = (),
        *,
        historical: tuple[float, ...] | None = None,
        projected: tuple[float, ...] | None = None,
        method: ForecastMethod = ForecastMethod.CAGR,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        growth_rates: tuple[float, ...] = (),
    ) -> None:
        if historical is not None or projected is not None:
            hist = tuple(float(value) for value in (historical or ()))
            proj = tuple(float(value) for value in (projected or ()))
            vals = proj
            yrs = tuple(range(1, len(proj) + 1))
        else:
            hist = ()
            proj = tuple(float(value) for value in values)
            vals = proj
            yrs = tuple(int(year) for year in years)
            if not yrs and proj:
                yrs = tuple(range(1, len(proj) + 1))
        if len(vals) != len(yrs):
            raise ForecastValidationError("values and years must have the same length")
        object.__setattr__(self, "values", vals)
        object.__setattr__(self, "years", yrs)
        object.__setattr__(self, "historical", hist)
        object.__setattr__(self, "projected", proj)
        object.__setattr__(self, "method", ForecastMethod(method))
        object.__setattr__(self, "confidence", ConfidenceLevel(confidence))
        object.__setattr__(self, "growth_rates", tuple(float(value) for value in growth_rates))

    def to_dict(self) -> dict[str, Any]:
        return {
            "values": list(self.values),
            "years": list(self.years),
            "historical": list(self.historical),
            "projected": list(self.projected),
            "method": self.method.value.lower(),
            "confidence": self.confidence.value.lower(),
            "growth_rates": list(self.growth_rates),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> _ForecastSeries:
        return cls(
            values=tuple(data.get("values", data.get("projected", ()))),
            years=tuple(data.get("years", range(1, len(data.get("projected", ())) + 1))),
            historical=tuple(data.get("historical", ())),
            projected=tuple(data.get("projected", ())),
            method=ForecastMethod(str(data.get("method", "CAGR")).upper()),
            confidence=ConfidenceLevel(str(data.get("confidence", "MEDIUM")).upper()),
            growth_rates=tuple(data.get("growth_rates", ())),
        )


@dataclass(frozen=True, slots=True, init=False)
class RevenueForecast(_ForecastSeries):
    pass


@dataclass(frozen=True, slots=True, init=False)
class MarginForecast(_ForecastSeries):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if any(value < 0.0 or value > 1.0 for value in self.values):
            raise ForecastValidationError("margin values must be between 0 and 1")


@dataclass(frozen=True, slots=True, init=False)
class CapexForecast(_ForecastSeries):
    pass


@dataclass(frozen=True, slots=True, init=False)
class DepreciationForecast(_ForecastSeries):
    pass


@dataclass(frozen=True, slots=True, init=False)
class WorkingCapitalForecast(_ForecastSeries):
    @property
    def delta(self) -> tuple[float, ...]:
        combined = self.historical + self.projected
        if not combined:
            return ()
        previous = self.historical[-1] if self.historical else 0.0
        return tuple((previous := value) - (self.historical[-1] if index == 0 else self.projected[index - 1]) for index, value in enumerate(self.projected))


@dataclass(frozen=True, slots=True, init=False)
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


@dataclass(frozen=True, slots=True, init=False)
class ForecastAssumption:
    revenue_growth_rate: float
    ebitda_margin: float
    tax_rate: float
    capex_pct_revenue: float
    working_capital_pct_revenue: float
    metadata: dict[str, Any]

    def __init__(
        self,
        revenue_growth_rate: float,
        ebitda_margin: float,
        tax_rate: float,
        capex_pct_revenue: float,
        working_capital_pct_revenue: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "revenue_growth_rate", float(revenue_growth_rate))
        object.__setattr__(self, "ebitda_margin", float(ebitda_margin))
        object.__setattr__(self, "tax_rate", float(tax_rate))
        object.__setattr__(self, "capex_pct_revenue", float(capex_pct_revenue))
        object.__setattr__(self, "working_capital_pct_revenue", float(working_capital_pct_revenue))
        object.__setattr__(self, "metadata", dict(metadata or {}))

    def to_dict(self) -> dict[str, Any]:
        return {
            "revenue_growth_rate": self.revenue_growth_rate,
            "ebitda_margin": self.ebitda_margin,
            "tax_rate": self.tax_rate,
            "capex_pct_revenue": self.capex_pct_revenue,
            "working_capital_pct_revenue": self.working_capital_pct_revenue,
            "metadata": dict(self.metadata),
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
            },
            metadata=dict(data.get("metadata", {})),
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
