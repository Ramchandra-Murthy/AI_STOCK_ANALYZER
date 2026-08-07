from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class InvestorScoreResult:
    symbol: str
    investor_name: str
    score: float
    recommendation: str
    rationale: Dict[str, Any]
    metadata: Dict[str, Any]
