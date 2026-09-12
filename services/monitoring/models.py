from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SystemHealthReport:
    status: str  # "HEALTHY", "DEGRADED", "CRITICAL"
    component_health: dict[str, str]
    metrics: dict[str, float]
    active_alerts: int
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
