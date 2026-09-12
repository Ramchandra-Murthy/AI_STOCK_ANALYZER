from services.scoring.investment_decision import InvestmentDecisionOrchestrator
from services.scoring.models import AIScoreResult


def test_block16c_position_sizing_allocation():
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

    orchestrator = InvestmentDecisionOrchestrator(
        policy_profile="Institutional", max_position_limit=0.10
    )
    result = orchestrator.evaluate(ai_score, holdings=None, current_weight=0.03)

    assert result.symbol == "TCS.NS"
    assert result.action in ["BUY", "STRONG BUY"]
    assert 0.0 <= result.target_weight <= 0.10
    assert result.incremental_weight == round(result.target_weight - 0.03, 4)
    assert result.details["engine_version"] == "EROS-3.0-BLOCK-16D"
    assert "sizing_metrics" in result.details
