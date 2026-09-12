from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AttributionReport:
    portfolio_id: str
    benchmark: str
    portfolio_return: float
    benchmark_return: float
    active_return: float
    allocation_effect: float
    selection_effect: float
    interaction_effect: float
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
