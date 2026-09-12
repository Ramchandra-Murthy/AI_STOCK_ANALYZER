from services.scoring.block18_orchestrator import UnifiedResearchToDecisionOrchestrator
from services.scoring.models import AIScoreResult


def test_block18_unified_orchestrator():
    ai_score = AIScoreResult(
        symbol="TCS.NS",
        growth_score=88.0,
        quality_score=91.0,
        profitability_score=90.0,
        capital_allocation_score=85.0,
        valuation_score=82.0,
        momentum_score=78.0,
        risk_score=86.0,
        composite_score=85.7,
        breakdown_details={
            "rating": "STRONG BUY",
            "engine_version": "EROS-3.0-BLOCK-15",
        },
    )

    orchestrator = UnifiedResearchToDecisionOrchestrator(
        policy_profile="Institutional", max_position_limit=0.10
    )
    result = orchestrator.evaluate(ai_score, holdings=None, portfolio_weight=0.03)

    assert result.symbol == "TCS.NS"
    assert result.final_action in ["BUY", "STRONG BUY", "HOLD"]
    assert 0.0 <= result.adjusted_confidence <= 1.0
    assert result.details["engine_version"] == "EROS-3.0-BLOCK-18"
    assert "research_intelligence" in result.details
    assert "evidence_reasoning" in result.details
    assert "research_confidence" in result.details
    assert "execution_summary" in result.details
    assert len(result.summary_rationale) > 0
