from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InvestorScoreResult:
    symbol: str
    investor_name: str
    score: float
    recommendation: str
    rationale: dict[str, Any]
    metadata: dict[str, Any]
