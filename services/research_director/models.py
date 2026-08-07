from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class ResearchMission:
    mission_id: str
    symbol: str
    priority: int # 1 = High, 5 = Low
    assigned_agents: List[str]
    status: str # "PENDING", "RUNNING", "COMPLETED", "FAILED"
    start_time: str
    completion_time: str | None
    workflow_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
