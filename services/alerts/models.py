from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class InstitutionalAlert:
    symbol: str
    alert_type: str
    severity: str  # "HIGH", "MEDIUM", "LOW"
    message: str
    acknowledged: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
