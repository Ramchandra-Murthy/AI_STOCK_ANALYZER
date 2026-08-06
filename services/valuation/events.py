from __future__ import annotations

from dataclasses import dataclass
from core.events.event import BaseDomainEvent


@dataclass(frozen=True, slots=True)
class ValuationCompleted(BaseDomainEvent):
    """Event emitted when valuation calculations are completed."""
    name: str = "valuation.completed"
