from __future__ import annotations

import pytest
from services.compliance.models import ComplianceReport
from services.compliance.policy_engine import InstitutionalCompliancePlatform

def test_compliance_report_immutability() -> None:
    rep = ComplianceReport(
        portfolio_id="P-001",
        compliant=True,
        violations=[],
        exposure_summary={"RELIANCE.NS": 0.30},
        mandate="Balanced",
        audit_id="A-001"
    )
    assert rep.portfolio_id == "P-001"
    assert rep.compliant is True
    assert rep.timestamp is not None
    assert isinstance(rep.metadata, dict)

def test_institutional_compliance_platform() -> None:
    holdings = [
        {"symbol": "RELIANCE.NS", "weight": 0.25},
        {"symbol": "TCS.NS", "weight": 0.25}
    ]
    report = InstitutionalCompliancePlatform.evaluate_compliance("P-002", holdings, "Balanced Institutional")
    assert report.portfolio_id == "P-002"
    assert report.compliant is True
    assert len(report.violations) == 0

    # Test violation case (> 0.35 limit)
    bad_holdings = [{"symbol": "CONCENTRATE.NS", "weight": 0.45}]
    bad_report = InstitutionalCompliancePlatform.evaluate_compliance("P-003", bad_holdings)
    assert bad_report.compliant is False
    assert len(bad_report.violations) > 0
