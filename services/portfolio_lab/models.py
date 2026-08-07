from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class PortfolioStrategy:
    strategy_name: str
    objective: str
    holdings: List[Dict[str, Any]]
    expected_return: float
    expected_volatility: float
    expected_sharpe: float
    turnover: float
    benchmark: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
