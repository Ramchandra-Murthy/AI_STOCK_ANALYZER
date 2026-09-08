from services.scoring.investment_decision import InvestmentDecisionOrchestrator
from services.scoring.models import AIScoreResult


def score(**overrides):
    values = dict(
        symbol="TEST.NS",
        growth_score=0.0,
        quality_score=0.0,
        profitability_score=0.0,
        capital_allocation_score=0.0,
        valuation_score=0.0,
        momentum_score=50.0,
        risk_score=80.0,
        composite_score=50.0,
        breakdown_details={
            "current_price": 100.0,
            "scoring_source": "canonical-live-market-packet",
            "observed_pillars": ["momentum", "market_risk"],
            "fundamental_pillars_available": False,
            "market_data_state": "LIVE",
        },
    )
    values.update(overrides)
    return AIScoreResult(**values)


def test_decision_does_not_invent_buy_thesis_from_symbol():
    result = InvestmentDecisionOrchestrator().evaluate(score())
    assert result.action == "HOLD"
    assert result.rating == "HOLD"
    assert all("Intrinsic value" not in item for item in result.rationale)


def test_high_evidence_score_can_produce_buy():
    result = InvestmentDecisionOrchestrator().evaluate(
        score(composite_score=82.0, momentum_score=84.0, risk_score=78.0)
    )
    assert result.action == "BUY"
    assert result.rating == "BUY"
    assert result.target_weight > 0.0
