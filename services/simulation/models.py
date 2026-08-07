from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class SimulationResult:
    scenario_id: str
    portfolio_return: float
    volatility: float
    max_drawdown: float
    sharpe_ratio: float
    value_at_risk: float
    execution_cost: float
    recommendation: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
