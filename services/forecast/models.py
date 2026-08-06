from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True, slots=True)
class FinancialMetricForecast:
    """Forecasted projections for a specific metric over future years."""
    metric_name: str
    historical_base: float
    projections: List[float] = field(default_factory=list)
    cagr: float = 0.0


@dataclass(frozen=True, slots=True)
class ForecastResult:
    """Complete financial forecast suite for a company."""
    symbol: str
    revenue: FinancialMetricForecast
    eps: FinancialMetricForecast
    fcf: FinancialMetricForecast
    ebitda: FinancialMetricForecast
    model_type: str = "DeterministicGrowthModel"
