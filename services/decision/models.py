from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class DecisionOption:
    """A decision candidate produced from validated analytical evidence."""

    option_id: str
    action: str
    confidence: float
    expected_return: float
    downside_risk: float
    rationale: list[str]
    evidence: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
