from __future__ import annotations

from dataclasses import dataclass
from core.events.event import BaseEvent


@dataclass(frozen=True, slots=True)
class ResearchCompleted(BaseEvent):
    """Event published when comprehensive equity research analysis is completed."""
    symbol: str = ""
    ai_recommendation: str = ""
    confidence_score: float = 0.0
    name: str = "research.completed"
