from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class ReasoningEvidence:
    source_node: str
    target_node: str
    relationship: str
    impact: str # e.g., "POSITIVE", "NEGATIVE", "NEUTRAL"
    confidence: float
    explanation: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
