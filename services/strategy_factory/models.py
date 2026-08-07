from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class StrategyResult:
    strategy_name: str
    investment_style: str
    selected_candidates: List[str]
    factor_tilts: Dict[str, float]
    expected_cagr: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
