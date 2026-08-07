from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class PortfolioAllocation:
    symbol: str
    target_weight: float
    expected_return: float
    expected_volatility: float
    expected_alpha: float
    conviction_score: float
    rationale: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
