from services.reporting.block19_report import Block19ReportGenerator
from services.scoring.block18_orchestrator import UnifiedResearchToDecisionOrchestrator
from services.scoring.models import AIScoreResult


def test_block19_report_generation():
    ai_score = AIScoreResult(
        symbol="INFY.NS",
        growth_score=86.0,
        quality_score=92.0,
        profitability_score=91.0,
        capital_allocation_score=84.0,
        valuation_score=80.0,
        momentum_score=76.0,
        risk_score=89.0,
        composite_score=86.2,
        breakdown_details={
            "rating": "STRONG BUY",
            "engine_version": "EROS-3.0-BLOCK-15",
        },
    )

    orchestrator = UnifiedResearchToDecisionOrchestrator(
        policy_profile="Institutional", max_position_limit=0.10
    )
    unified_result = orchestrator.evaluate(ai_score, holdings=None, portfolio_weight=0.02)

    markdown_report = Block19ReportGenerator.generate_markdown(unified_result)

    assert isinstance(markdown_report, str)
    assert "# EROS 3.0 — INSTITUTIONAL INVESTMENT REPORT" in markdown_report
    assert "INFY.NS" in markdown_report
    assert "STRONG BUY" in markdown_report or "BUY" in markdown_report
    assert "Executive Summary" in markdown_report
    assert "Quantitative Pillar Breakdown" in markdown_report
    assert "Economic Moat" in markdown_report
    assert "Portfolio Allocation & Execution" in markdown_report
