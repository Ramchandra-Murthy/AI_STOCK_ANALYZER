from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class InvestmentOpportunity:
    symbol: str
    thesis: str
    expected_return: float
    conviction: float
    quality_score: float
    valuation_score: float
    momentum_score: float
    catalyst_score: float
    risk_score: float
    priority: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
