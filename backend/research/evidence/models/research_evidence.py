from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class ResearchEvidence:
    """
    Structured institutional evidence attached to a ResearchCase.
    Evidence is deliberately separated from the research conclusion.
    It represents an observable fact, analytical observation, or
    externally sourced research statement that can later contribute
    to investment reasoning.
    """

    evidence_id: str
    case_id: str
    symbol: str
    category: str
    statement: str
    value: Any = None
    source: str = "EROS"
    source_type: str = "INTERNAL"
    confidence: float = 1.0
    materiality: float = 0.5
    recency: float = 1.0
    polarity: str = "NEUTRAL"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise ValueError("evidence_id is required")
        if not self.case_id:
            raise ValueError("case_id is required")
        if not self.symbol:
            raise ValueError("symbol is required")
        if not self.category:
            raise ValueError("category is required")
        if not self.statement:
            raise ValueError("statement is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if not 0.0 <= self.materiality <= 1.0:
            raise ValueError("materiality must be between 0.0 and 1.0")
        if not 0.0 <= self.recency <= 1.0:
            raise ValueError("recency must be between 0.0 and 1.0")
        allowed_polarities = {
            "POSITIVE",
            "NEGATIVE",
            "NEUTRAL",
        }
        if self.polarity not in allowed_polarities:
            raise ValueError("polarity must be POSITIVE, NEGATIVE, or NEUTRAL")
