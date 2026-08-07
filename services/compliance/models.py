from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class ComplianceReport:
    portfolio_id: str
    compliant: bool
    violations: List[str]
    exposure_summary: Dict[str, float]
    mandate: str
    audit_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
