from __future__ import annotations

from dataclasses import dataclass
from core.events.event import BaseEvent


@dataclass(frozen=True, slots=True)
class ReportCompleted(BaseEvent):
    """Event published when multi-format report generation is completed."""
    symbol: str = ""
    format_type: str = ""
    name: str = "report.completed"
