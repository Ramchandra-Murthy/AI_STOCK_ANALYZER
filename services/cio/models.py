from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class InvestmentDecision:
    symbol: str
    decision: str # "BUY", "SELL", "HOLD"
    conviction: float
    position_size: float
    expected_return: float
    expected_risk: float
    target_price: float
    holding_period: str
    committee_votes: Dict[str, str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
