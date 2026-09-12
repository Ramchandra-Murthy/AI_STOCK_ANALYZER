from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CorporateEvent:
    event_id: str
    symbol: str
    event_type: str  # e.g. "CEO_CHANGE", "ACQUISITION", "DIVIDEND", "RIGHTS_ISSUE", "REGULATORY"
    title: str
    description: str
    date: str
    impact_score: float = 0.0  # -1.0 to 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class CompanyTimelineEngine:
    """Manages the chronological corporate history and milestone timeline for companies."""

    def __init__(self) -> None:
        self._timelines: dict[str, list[CorporateEvent]] = {}

    def add_event(self, event: CorporateEvent) -> None:
        if event.symbol not in self._timelines:
            self._timelines[event.symbol] = []
        self._timelines[event.symbol].append(event)
        # Sort chronologically by date
        self._timelines[event.symbol].sort(key=lambda x: x.date)

    def get_timeline(self, symbol: str) -> list[CorporateEvent]:
        return self._timelines.get(symbol, [])
