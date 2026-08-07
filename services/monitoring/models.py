from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class SystemHealthReport:
    status: str # "HEALTHY", "DEGRADED", "CRITICAL"
    component_health: Dict[str, str]
    metrics: Dict[str, float]
    active_alerts: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
