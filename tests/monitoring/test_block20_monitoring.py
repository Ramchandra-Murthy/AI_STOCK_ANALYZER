from services.scoring.models import AIScoreResult
from services.scoring.block18_orchestrator import UnifiedResearchToDecisionOrchestrator
from services.monitoring.investment_monitor import InvestmentMonitor
from services.monitoring.change_detector import InvestmentChangeDetector

def test_block20_monitoring_and_change_detection():
    ai_score_prev = AIScoreResult(
        symbol="HDFC.NS",
        growth_score=80.0,
        quality_score=85.0,
        profitability_score=82.0,
        capital_allocation_score=78.0,
        valuation_score=75.0,
        momentum_score=70.0,
        risk_score=85.0,
        composite_score=79.4,
        breakdown_details={"rating": "BUY"}
    )

    orchestrator = UnifiedResearchToDecisionOrchestrator(policy_profile="Institutional")
    res_prev = orchestrator.evaluate(ai_score_prev, holdings=None, portfolio_weight=0.05)

    snap_prev = InvestmentMonitor.capture_snapshot(res_prev)
    assert snap_prev.symbol == "HDFC.NS"
    assert snap_prev.composite_score == 79.4

    ai_score_curr = AIScoreResult(
        symbol="HDFC.NS",
        growth_score=80.0,
        quality_score=85.0,
        profitability_score=82.0,
        capital_allocation_score=78.0,
        valuation_score=75.0,
        momentum_score=50.0,
        risk_score=60.0,
        composite_score=70.8,
        breakdown_details={"rating": "HOLD"}
    )

    res_curr = orchestrator.evaluate(ai_score_curr, holdings=None, portfolio_weight=0.02)
    snap_curr = InvestmentMonitor.capture_snapshot(res_curr)

    report = InvestmentChangeDetector.detect_changes(snap_prev, snap_curr)
    assert report.symbol == "HDFC.NS"
    assert report.changes_detected > 0
    assert report.high_severity_changes >= 1
    assert report.details["engine_version"] == "EROS-3.0-BLOCK-20B"
