from __future__ import annotations

from dataclasses import dataclass
from core.events.event import BaseEvent


@dataclass(frozen=True, slots=True)
class ValuationCompleted(BaseEvent):
    """Event published when multi-model valuation analysis is completed."""
    symbol: str = ""
    blended_fair_value: float = 0.0
    margin_of_safety_pct: float = 0.0
    recommendation: str = ""
    name: str = "valuation.completed"
