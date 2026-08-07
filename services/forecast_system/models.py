from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class ForecastResult:
    symbol: str
    revenue_forecast: float
    ebit_forecast: float
    eps_forecast: float
    fcf_forecast: float
    forecast_confidence: float
    bull_case_eps: float
    base_case_eps: float
    bear_case_eps: float
    key_assumptions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
