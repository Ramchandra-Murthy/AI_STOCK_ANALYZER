from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class WorkflowResult:
    run_id: str
    completed_steps: list[str]
    failed_steps: list[str]
    execution_time: float
    reports_generated: list[str]
    warnings: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
