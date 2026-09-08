from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True, slots=True)
class AIScoreResult:
    """Multi-pillar institutional AI Scoring Result."""
    symbol: str
    growth_score: float
    quality_score: float
    profitability_score: float
    capital_allocation_score: float
    valuation_score: float
    momentum_score: float
    risk_score: float
    composite_score: float
    breakdown_details: Dict[str, Any] = field(default_factory=dict)
