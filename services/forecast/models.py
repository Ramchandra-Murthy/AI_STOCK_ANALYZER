from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class FinancialMetricForecast:
    """Forecast details for an individual financial metric."""

    metric_name: str
    historical_values: list[float] = field(default_factory=list)
    projected_values: list[float] = field(default_factory=list)
    growth_rate: float = 0.10
    model_used: str = "CAGR"


@dataclass(frozen=True, slots=True)
class ForecastResult:
    """Comprehensive multi-period forecast result based on financial statements."""

    symbol: str
    model_type: str
    forecast_periods: int = 5
    revenue_forecast: list[float] = field(default_factory=list)
    ebit_forecast: list[float] = field(default_factory=list)
    eps_forecast: list[float] = field(default_factory=list)
    free_cash_flow_forecast: list[float] = field(default_factory=list)
    capex_forecast: list[float] = field(default_factory=list)
    working_capital_forecast: list[float] = field(default_factory=list)
    depreciation_forecast: list[float] = field(default_factory=list)
    assumptions: dict[str, Any] = field(default_factory=dict)
