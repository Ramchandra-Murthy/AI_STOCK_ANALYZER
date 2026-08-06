from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True, slots=True)
class FinancialMetricForecast:
    """Forecast details for an individual financial metric (e.g., Revenue, EBIT)."""
    metric_name: str
    historical_values: List[float] = field(default_factory=list)
    projected_values: List[float] = field(default_factory=list)
    growth_rate: float = 0.10
    model_used: str = "CAGR"


@dataclass(frozen=True, slots=True)
class ForecastResult:
    """Comprehensive multi-period forecast result based on financial statements."""
    symbol: str
    model_type: str
    forecast_periods: int = 5
    revenue_forecast: List[float] = field(default_factory=list)
    ebit_forecast: List[float] = field(default_factory=list)
    eps_forecast: List[float] = field(default_factory=list)
    free_cash_flow_forecast: List[float] = field(default_factory=list)
    capex_forecast: List[float] = field(default_factory=list)
    working_capital_forecast: List[float] = field(default_factory=list)
    depreciation_forecast: List[float] = field(default_factory=list)
    assumptions: Dict[str, Any] = field(default_factory=dict)
