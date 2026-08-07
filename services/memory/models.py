from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

@dataclass(frozen=True)
class ResearchMemory:
    symbol: str
    research_date: str
    summary: str
    committee_decision: str
    valuation_snapshot: Dict[str, float]
    forecast_snapshot: Dict[str, float]
    thesis: str
    outcome: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
