from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class WorkflowResult:
    run_id: str
    completed_steps: List[str]
    failed_steps: List[str]
    execution_time: float
    reports_generated: List[str]
    warnings: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
