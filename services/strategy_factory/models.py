from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class StrategyResult:
    strategy_name: str
    investment_style: str
    selected_candidates: list[str]
    factor_tilts: dict[str, float]
    expected_cagr: float
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
