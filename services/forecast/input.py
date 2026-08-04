"""
==========================================================
FORECAST INPUT CONTRACTS
Module  : services.forecast.input
Layer   : Forecast Service Input
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Tuple, Dict, Any, Mapping, Type, TypeVar
from services.forecast.models import ForecastMethod, ScenarioType, ForecastFrequency
from services.forecast.exceptions import (
    ForecastValidationError,
    ForecastSerializationError,
)

T = TypeVar("T", bound="ForecastInput")


@dataclass(frozen=True, slots=True)
class ForecastInput:
    """Canonical immutable input contract for generating financial forecasts."""

    ticker: str
    historical_years: Tuple[int, ...]
    historical_revenue: Tuple[float, ...]
    historical_margins: Tuple[float, ...]
    historical_capex: Tuple[float, ...]
    historical_depreciation: Tuple[float, ...]
    historical_working_capital: Tuple[float, ...]
    historical_taxes: Tuple[float, ...]
    forecast_years: Tuple[int, ...]
    method: ForecastMethod = ForecastMethod.CAGR
    scenario_type: ScenarioType = ScenarioType.BASE
    frequency: ForecastFrequency = ForecastFrequency.ANNUAL
    custom_growth_rate: float | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.ticker or not self.ticker.strip():
            raise ForecastValidationError("Ticker symbol must be a non-empty string.")

        hist_len = len(self.historical_years)
        if hist_len == 0:
            raise ForecastValidationError("Historical years sequence cannot be empty.")

        if any(
            len(seq) != hist_len
            for seq in [
                self.historical_revenue,
                self.historical_margins,
                self.historical_capex,
                self.historical_depreciation,
                self.historical_working_capital,
                self.historical_taxes,
            ]
        ):
            raise ForecastValidationError(
                "All historical data series must match the length of historical_years."
            )

        if len(self.forecast_years) == 0:
            raise ForecastValidationError("Forecast years sequence cannot be empty.")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls: Type[T], data: Mapping[str, object]) -> T:
        try:
            return cls(
                ticker=str(data["ticker"]),
                historical_years=tuple(int(y) for y in data["historical_years"]),  # type: ignore
                historical_revenue=tuple(float(v) for v in data["historical_revenue"]),  # type: ignore
                historical_margins=tuple(float(v) for v in data["historical_margins"]),  # type: ignore
                historical_capex=tuple(float(v) for v in data["historical_capex"]),  # type: ignore
                historical_depreciation=tuple(float(v) for v in data["historical_depreciation"]),  # type: ignore
                historical_working_capital=tuple(float(v) for v in data["historical_working_capital"]),  # type: ignore
                historical_taxes=tuple(float(v) for v in data["historical_taxes"]),  # type: ignore
                forecast_years=tuple(int(y) for y in data["forecast_years"]),  # type: ignore
                method=ForecastMethod(
                    str(data.get("method", ForecastMethod.CAGR.value))
                ),
                scenario_type=ScenarioType(
                    str(data.get("scenario_type", ScenarioType.BASE.value))
                ),
                frequency=ForecastFrequency(
                    str(data.get("frequency", ForecastFrequency.ANNUAL.value))
                ),
                custom_growth_rate=(
                    float(data["custom_growth_rate"])
                    if data.get("custom_growth_rate") is not None
                    else None
                ),
                metadata=dict(data.get("metadata", {})),  # type: ignore
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ForecastSerializationError(
                f"Failed to deserialize ForecastInput: {e}"
            ) from e
