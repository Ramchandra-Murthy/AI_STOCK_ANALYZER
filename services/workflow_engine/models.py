from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class WorkflowExecution:
    workflow_id: str
    symbol: str
    execution_time: str
    completed_steps: List[str]
    failed_steps: List[str]
    total_runtime: float
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
