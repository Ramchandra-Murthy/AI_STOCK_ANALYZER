from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
