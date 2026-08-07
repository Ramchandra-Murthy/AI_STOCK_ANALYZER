from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

@dataclass(frozen=True)
class WatchlistItem:
    symbol: str
    priority: int
    investment_thesis: str
    current_recommendation: str
    committee_score: float
    latest_catalyst: str
    major_risks: List[str]
    next_earnings_date: str
    alert_status: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
