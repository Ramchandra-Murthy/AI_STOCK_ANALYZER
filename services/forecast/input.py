from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, Any

@dataclass(frozen=True, slots=True)
class ForecastInput:
    ticker: str
    historical_years: Tuple[int, ...]
    historical_revenue: Tuple[float, ...]
    historical_margins: Tuple[float, ...]
    historical_capex: Tuple[float, ...]
    historical_depreciation: Tuple[float, ...]
    historical_working_capital: Tuple[float, ...]
    historical_taxes: Tuple[float, ...]
    forecast_years: Tuple[int, ...]
    custom_growth_rate: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
