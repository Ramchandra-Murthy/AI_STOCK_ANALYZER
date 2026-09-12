from services.governance.audit_trail import AuditTrailGenerator
from services.governance.governance_engine import GovernanceEngine
from services.monitoring.change_detector import InvestmentChangeDetector
from services.monitoring.investment_monitor import InvestmentMonitor
from services.reporting.block19_report import Block19ReportGenerator
from services.scoring.block18_orchestrator import UnifiedResearchToDecisionOrchestrator
from services.scoring.models import AIScoreResult
from services.validation.backtest_engine import InstitutionalBacktestEngine


def test_block21c_e2e_production_lifecycle():
    # 1. Generate AI Score
    ai_score = AIScoreResult(
        symbol="WIPRO.NS",
        growth_score=85.0,
        quality_score=90.0,
        profitability_score=88.0,
        capital_allocation_score=82.0,
        valuation_score=80.0,
        momentum_score=78.0,
        risk_score=87.0,
        composite_score=84.3,
        breakdown_details={"rating": "STRONG BUY"},
    )

    # 2. Unified Research-to-Decision Orchestration (Blocks 16-18)
    orchestrator = UnifiedResearchToDecisionOrchestrator(
        policy_profile="Institutional", max_position_limit=0.10
    )
    unified_result = orchestrator.evaluate(ai_score, holdings=None, portfolio_weight=0.04)
    assert unified_result.symbol == "WIPRO.NS"

    # 3. Institutional Report Generation (Block 19)
    markdown_report = Block19ReportGenerator.generate_markdown(unified_result)
    assert "# EROS 3.0" in markdown_report
    assert "WIPRO.NS" in markdown_report

    # 4. Monitoring & Change Detection (Block 20A-B)
    snap_prev = InvestmentMonitor.capture_snapshot(unified_result)

    # Simulate a degraded subsequent state
    ai_score_curr = AIScoreResult(
        symbol="WIPRO.NS",
        growth_score=85.0,
        quality_score=90.0,
        profitability_score=88.0,
        capital_allocation_score=82.0,
        valuation_score=80.0,
        momentum_score=45.0,
        risk_score=55.0,
        composite_score=72.0,
        breakdown_details={"rating": "HOLD"},
    )
    unified_result_curr = orchestrator.evaluate(ai_score_curr, holdings=None, portfolio_weight=0.02)
    snap_curr = InvestmentMonitor.capture_snapshot(unified_result_curr)

    change_report = InvestmentChangeDetector.detect_changes(snap_prev, snap_curr)
    assert change_report.changes_detected > 0

    # 5. Governance & Audit Trail (Block 20C-E)
    holdings = [{"symbol": "WIPRO.NS", "weight": 0.04}]
    gov_event, compliance_rep = GovernanceEngine.evaluate_governance(
        change_report, holdings, portfolio_id="PORT-PROD-01"
    )
    audit_record = AuditTrailGenerator.generate_audit_record(gov_event, compliance_rep)
    assert audit_record.compliant is True

    # 6. Backtest Validation (Block 21B)
    backtest_engine = InstitutionalBacktestEngine()
    backtest_res = backtest_engine.evaluate_signal(
        symbol="WIPRO.NS", signal_date="2026-01-01", entry_price=500.0, exit_price=575.0
    )
    assert backtest_res.accuracy is True
    assert backtest_res.return_pct == 15.0
