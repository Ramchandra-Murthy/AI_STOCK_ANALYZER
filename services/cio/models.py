from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class InvestmentDecision:
    symbol: str
    decision: str  # "BUY", "SELL", "HOLD"
    conviction: float
    position_size: float
    expected_return: float
    expected_risk: float
    target_price: float
    holding_period: str
    committee_votes: dict[str, str]
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
