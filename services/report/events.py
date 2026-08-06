from __future__ import annotations

from dataclasses import dataclass
from core.events.event import BaseDomainEvent


@dataclass(frozen=True, slots=True)
class ReportCompleted(BaseDomainEvent):
    """Event emitted when multi-format report generation is completed."""
    name: str = "report.completed"
    format_type: str = "MULTI-FORMAT"
