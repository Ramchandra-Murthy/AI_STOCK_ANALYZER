from services.scoring.investment_decision import InvestmentDecisionOrchestrator
from services.scoring.models import AIScoreResult


def test_block16_investment_decision_orchestrator():
    ai_score = AIScoreResult(
        symbol="INFY.NS",
        growth_score=85.0,
        quality_score=90.0,
        profitability_score=92.0,
        capital_allocation_score=80.0,
        valuation_score=78.0,
        momentum_score=75.0,
        risk_score=88.0,
        composite_score=84.5,
        breakdown_details={
            "rating": "STRONG BUY",
            "engine_version": "EROS-3.0-BLOCK-15",
        },
    )

    orchestrator = InvestmentDecisionOrchestrator(policy_profile="Institutional")
    result = orchestrator.evaluate(ai_score, portfolio_weight=0.05)

    assert result.symbol == "INFY.NS"
    assert result.action in ["BUY", "HOLD", "SELL"]
    assert 0.0 <= result.confidence <= 1.0
    assert result.composite_score == 84.5
    assert result.rating == "STRONG BUY"
    assert result.details["engine_version"] == "EROS-3.0-BLOCK-16D"
    assert len(result.rationale) > 0
    assert len(result.evidence) > 0
