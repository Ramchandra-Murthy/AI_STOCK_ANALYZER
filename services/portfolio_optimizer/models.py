from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class PortfolioAllocation:
    symbol: str
    target_weight: float
    expected_return: float
    expected_volatility: float
    expected_alpha: float
    conviction_score: float
    rationale: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
