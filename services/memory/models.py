from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ResearchMemory:
    symbol: str
    research_date: str
    summary: str
    committee_decision: str
    valuation_snapshot: dict[str, float]
    forecast_snapshot: dict[str, float]
    thesis: str
    outcome: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
