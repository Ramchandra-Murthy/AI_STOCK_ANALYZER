from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class ManagedPortfolio:
    portfolio_id: str
    strategy: str
    benchmark: str
    holdings: List[Dict[str, Any]]
    target_weights: Dict[str, float]
    cash_position: float
    expected_return: float
    expected_risk: float
    expected_tracking_error: float
    rebalance_required: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
