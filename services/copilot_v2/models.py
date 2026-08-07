from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class CopilotResponse:
    query: str
    answer: str
    confidence: float
    cited_engines: List[str]
    supporting_evidence: List[str]
    recommended_actions: List[str]
    follow_up_questions: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
