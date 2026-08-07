from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class EconomicMoatResult:
    symbol: str
    moat_score: float
    moat_classification: str
    factors: Dict[str, float]
    metadata: Dict[str, Any]
