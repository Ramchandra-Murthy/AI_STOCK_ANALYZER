from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class FinancialRatios:
    symbol: str
    period: str
    profitability: Dict[str, float]
    liquidity: Dict[str, float]
    solvency: Dict[str, float]
    efficiency: Dict[str, float]
    growth: Dict[str, float]
    cash_flow: Dict[str, float]
    quality_scores: Dict[str, float]
    metadata: Dict[str, Any]
