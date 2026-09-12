from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class WorkflowExecution:
    workflow_id: str
    symbol: str
    execution_time: str
    completed_steps: list[str]
    failed_steps: list[str]
    total_runtime: float
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
