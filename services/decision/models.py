from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class DecisionOption:
    option_id: str
    action: str # "BUY", "HOLD", "SELL"
    confidence: float
    expected_return: float
    downside_risk: float
    rationale: List[str]
    evidence: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
