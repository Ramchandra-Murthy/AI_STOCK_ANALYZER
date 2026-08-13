from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
from datetime import datetime
from services.monitoring.change_detector import ChangeDetectionReport
from services.compliance.policy_engine import InstitutionalCompliancePlatform
from services.compliance.models import ComplianceReport

@dataclass(frozen=True, slots=True)
class GovernanceEvent:
    event_id: str
    symbol: str
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    requires_manual_review: bool
    triggers: List[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)

class GovernanceEngine:
    """
    EROS 3.0 Block 20C Governance Engine.
    Evaluates change detection reports and portfolio holdings against compliance mandates and governance rules.
    """
    @staticmethod
    def evaluate_governance(report: ChangeDetectionReport, holdings: List[Dict[str, Any]], portfolio_id: str = "PORTFOLIO-INSTITUTIONAL-01") -> tuple[GovernanceEvent, ComplianceReport]:
        triggers: List[str] = []
        max_severity = "LOW"

        # 1. Analyze Change Report triggers
        for change in report.changes:
            if change.metric == "Action Change":
                triggers.append(f"Critical Action Shift: {change.reason}")
                max_severity = "CRITICAL"
            elif change.metric == "Rating Change":
                triggers.append(f"Rating Deviation: {change.reason}")
                if max_severity not in ("CRITICAL",):
                    max_severity = "HIGH"
            elif change.metric == "Risk Score" and change.direction == "DETERIORATED":
                triggers.append(f"Risk Deterioration: {change.reason}")
                if max_severity not in ("CRITICAL", "HIGH"):
                    max_severity = "HIGH"
            elif change.severity in ("HIGH", "CRITICAL"):
                triggers.append(f"High Severity Deviation ({change.metric}): {change.reason}")
                if max_severity not in ("CRITICAL",):
                    max_severity = change.severity

        requires_review = max_severity in ("HIGH", "CRITICAL") or report.high_severity_changes > 0

        event = GovernanceEvent(
            event_id=f"GOV-{report.symbol}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            symbol=report.symbol,
            severity=max_severity,
            requires_manual_review=requires_review,
            triggers=triggers,
            details={
                "engine_version": "EROS-3.0-BLOCK-20C",
                "changes_analyzed": report.changes_detected,
            }
        )

        # 2. Integrate with existing Institutional Compliance Platform
        compliance_rep = InstitutionalCompliancePlatform.evaluate_compliance(
            portfolio_id=portfolio_id,
            holdings=holdings,
            mandate="Strict Institutional Governance Mandate"
        )

        return event, compliance_rep
