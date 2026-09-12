from services.risk_management.models import PortfolioRiskProfile
from services.scoring.risk_scoring import RiskScoringEngine


def test_block15_risk_scoring_engine():
    profile = PortfolioRiskProfile(
        portfolio_id="PORT-001",
        expected_volatility=0.18,
        value_at_risk=0.05,
        expected_shortfall=0.08,
        concentration_score=75.0,
        liquidity_score=85.0,
        diversification_score=80.0,
        resilience_score=90.0,
    )
    engine = RiskScoringEngine()
    result = engine.evaluate("INFY.NS", profile)

    assert result.symbol == "INFY.NS"
    assert 0.0 <= result.risk_score <= 100.0
    assert 0.0 <= result.resilience_score <= 100.0
    assert result.details["engine_version"] == "EROS-3.0-BLOCK-15"
    assert "stress_test" in result.details
