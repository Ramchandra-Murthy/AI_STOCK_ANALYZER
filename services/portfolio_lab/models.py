from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class PortfolioStrategy:
    strategy_name: str
    objective: str
    holdings: list[dict[str, Any]]
    expected_return: float
    expected_volatility: float
    expected_sharpe: float
    turnover: float
    benchmark: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
