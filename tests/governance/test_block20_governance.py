from services.governance.audit_trail import AuditTrailGenerator
from services.governance.governance_engine import GovernanceEngine
from services.monitoring.change_detector import InvestmentChangeDetector
from services.monitoring.investment_monitor import InvestmentMonitor
from services.scoring.block18_orchestrator import UnifiedResearchToDecisionOrchestrator
from services.scoring.models import AIScoreResult


def test_block20_governance_and_audit():
    ai_score_prev = AIScoreResult(
        symbol="ITC.NS",
        growth_score=82.0,
        quality_score=88.0,
        profitability_score=85.0,
        capital_allocation_score=80.0,
        valuation_score=78.0,
        momentum_score=75.0,
        risk_score=90.0,
        composite_score=83.5,
        breakdown_details={"rating": "BUY"},
    )

    orchestrator = UnifiedResearchToDecisionOrchestrator(policy_profile="Institutional")
    res_prev = orchestrator.evaluate(ai_score_prev, holdings=None, portfolio_weight=0.08)
    snap_prev = InvestmentMonitor.capture_snapshot(res_prev)

    ai_score_curr = AIScoreResult(
        symbol="ITC.NS",
        growth_score=82.0,
        quality_score=88.0,
        profitability_score=85.0,
        capital_allocation_score=80.0,
        valuation_score=78.0,
        momentum_score=40.0,
        risk_score=50.0,
        composite_score=71.2,
        breakdown_details={"rating": "HOLD"},
    )

    res_curr = orchestrator.evaluate(ai_score_curr, holdings=None, portfolio_weight=0.04)
    snap_curr = InvestmentMonitor.capture_snapshot(res_curr)

    report = InvestmentChangeDetector.detect_changes(snap_prev, snap_curr)

    holdings = [{"symbol": "ITC.NS", "weight": 0.08}]
    gov_event, compliance_rep = GovernanceEngine.evaluate_governance(
        report, holdings, portfolio_id="PORT-INST-01"
    )

    assert gov_event.symbol == "ITC.NS"
    assert gov_event.requires_manual_review is True
    assert compliance_rep.portfolio_id == "PORT-INST-01"
    assert compliance_rep.compliant is True

    audit_rec = AuditTrailGenerator.generate_audit_record(gov_event, compliance_rep)
    assert audit_rec.symbol == "ITC.NS"
    assert audit_rec.governance_severity in ("HIGH", "CRITICAL")
    assert audit_rec.details["engine_version"] == "EROS-3.0-BLOCK-20E"
