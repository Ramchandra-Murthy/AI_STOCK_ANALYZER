from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class CopilotResponse:
    answer: str
    evidence: list[str]
    workflow_steps: list[str]
    confidence: float
    sources: list[str]
    follow_up_questions: list[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
