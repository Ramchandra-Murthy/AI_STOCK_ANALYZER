from services.scoring.investment_decision import InvestmentDecisionOrchestrator
from services.scoring.models import AIScoreResult


def test_block16d_execution_tca_integration():
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

    orchestrator = InvestmentDecisionOrchestrator(
        policy_profile="Institutional", max_position_limit=0.10
    )
    result = orchestrator.evaluate(ai_score, holdings=None, current_weight=0.02)

    assert result.symbol == "INFY.NS"
    assert result.action in ["BUY", "STRONG BUY"]
    assert result.target_weight > 0.02
    assert result.incremental_weight > 0.0
    assert result.execution_cost > 0.0
    assert result.details["engine_version"] == "EROS-3.0-BLOCK-16D"
    assert "execution_details" in result.details
    assert len(result.details["execution_details"]["generated_orders"]) > 0
    assert "transaction_cost_analysis" in result.details["execution_details"]
