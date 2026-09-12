from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ManagedPortfolio:
    portfolio_id: str
    strategy: str
    benchmark: str
    holdings: list[dict[str, Any]]
    target_weights: dict[str, float]
    cash_position: float
    expected_return: float
    expected_risk: float
    expected_tracking_error: float
    rebalance_required: bool
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
