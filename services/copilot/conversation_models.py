from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class CopilotResponse:
    answer: str
    evidence: List[str]
    workflow_steps: List[str]
    confidence: float
    sources: List[str]
    follow_up_questions: List[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
