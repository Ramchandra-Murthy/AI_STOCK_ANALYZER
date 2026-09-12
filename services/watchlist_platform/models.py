from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class WatchlistItem:
    symbol: str
    priority: int
    investment_thesis: str
    current_recommendation: str
    committee_score: float
    latest_catalyst: str
    major_risks: list[str]
    next_earnings_date: str
    alert_status: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
