from __future__ import annotations

from dataclasses import dataclass
from core.events.event import BaseDomainEvent


@dataclass(frozen=True, slots=True)
class ResearchCompleted(BaseDomainEvent):
    """Event emitted when research and thesis generation are completed."""
    name: str = "research.completed"
