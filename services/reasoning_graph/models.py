from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ReasoningEvidence:
    source_node: str
    target_node: str
    relationship: str
    impact: str  # e.g., "POSITIVE", "NEGATIVE", "NEUTRAL"
    confidence: float
    explanation: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
