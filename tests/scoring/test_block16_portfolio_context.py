from services.scoring.investment_decision import InvestmentDecisionOrchestrator
from services.scoring.models import AIScoreResult


def test_block16b_portfolio_context_integration():
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

    # Simulate existing portfolio holdings where INFY.NS is oversized (e.g., 20% of portfolio)
    holdings = {
        "INFY.NS": {"shares": 2000, "price": 1800.0, "cost_basis": 1500.0},
        "RELIANCE.NS": {"shares": 1000, "price": 2500.0, "cost_basis": 2400.0},
    }

    orchestrator = InvestmentDecisionOrchestrator(policy_profile="Institutional")
    result = orchestrator.evaluate(ai_score, holdings=holdings)

    assert result.symbol == "INFY.NS"
    assert result.portfolio_weight > 0.15
    assert result.action == "HOLD"  # Downgraded due to concentration limit check
    assert result.details["engine_version"] == "EROS-3.0-BLOCK-16D"
    assert "portfolio_context" in result.details
    assert len(result.rationale) > 1
