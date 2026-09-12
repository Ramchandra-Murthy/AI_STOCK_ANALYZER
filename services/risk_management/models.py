from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class PortfolioRiskProfile:
    portfolio_id: str
    expected_volatility: float
    value_at_risk: float
    expected_shortfall: float
    concentration_score: float
    liquidity_score: float
    diversification_score: float
    resilience_score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
