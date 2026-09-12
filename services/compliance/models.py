from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ComplianceReport:
    portfolio_id: str
    compliant: bool
    violations: list[str]
    exposure_summary: dict[str, float]
    mandate: str
    audit_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
