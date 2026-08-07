from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class ForecastScenario:
    scenario_id: str
    name: str # e.g. "BULL", "BASE", "BEAR"
    probability: float # 0.0 to 1.0
    revenue_growth: float
    margin: float
    wacc: float
    terminal_growth: float
    inflation: float
    interest_rate: float
    intrinsic_value: float
    expected_return: float
    risk_score: float

@dataclass(frozen=True)
class ForecastResult:
    symbol: str
    expected_value: float
    bull_value: float
    base_value: float
    bear_value: float
    confidence: float
    probability_distribution: Dict[str, float]
    key_drivers: List[str]
    major_risks: List[str]
    assumptions: List[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
