from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any

@dataclass(frozen=True)
class WorkflowContext:
    workflow_id: str
    symbol: str
    user: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    shared_data: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)