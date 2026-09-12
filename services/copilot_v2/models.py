from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CopilotResponse:
    query: str
    answer: str
    confidence: float
    cited_engines: list[str]
    supporting_evidence: list[str]
    recommended_actions: list[str]
    follow_up_questions: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
