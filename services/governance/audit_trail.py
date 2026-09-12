from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from services.compliance.models import ComplianceReport
from services.governance.governance_engine import GovernanceEvent


@dataclass(frozen=True, slots=True)
class AuditRecord:
    audit_id: str
    symbol: str
    portfolio_id: str
    compliant: bool
    governance_severity: str
    requires_manual_review: bool
    triggers: list[str]
    violations: list[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    details: dict[str, Any] = field(default_factory=dict)


class AuditTrailGenerator:
    """
    EROS 3.0 Block 20E Audit Trail Generator.
    Bundles governance events and compliance reports into tamper-evident audit records.
    """

    @staticmethod
    def generate_audit_record(event: GovernanceEvent, compliance: ComplianceReport) -> AuditRecord:
        audit_id = f"AUDIT-REC-{event.symbol}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        return AuditRecord(
            audit_id=audit_id,
            symbol=event.symbol,
            portfolio_id=compliance.portfolio_id,
            compliant=compliance.compliant,
            governance_severity=event.severity,
            requires_manual_review=event.requires_manual_review,
            triggers=event.triggers,
            violations=compliance.violations,
            details={
                "engine_version": "EROS-3.0-BLOCK-20E",
                "governance_event_id": event.event_id,
                "compliance_audit_id": compliance.audit_id,
                "mandate": compliance.mandate,
                "exposure_summary": compliance.exposure_summary,
            },
        )
