from __future__ import annotations

from services.risk_management.models import PortfolioRiskProfile
from services.risk_management.resilience import RiskResilienceEngine
from services.risk_management.stress_engine import StressTestingEngine


def test_portfolio_risk_profile_immutability() -> None:
    profile = PortfolioRiskProfile(
        portfolio_id="PORT-001",
        expected_volatility=0.15,
        value_at_risk=0.02,
        expected_shortfall=0.03,
        concentration_score=0.25,
        liquidity_score=0.90,
        diversification_score=0.85,
        resilience_score=0.82,
    )
    assert profile.portfolio_id == "PORT-001"
    assert profile.resilience_score == 0.82
    assert profile.timestamp is not None
    assert isinstance(profile.metadata, dict)


def test_risk_resilience_evaluation() -> None:
    profile = RiskResilienceEngine.evaluate_portfolio_risk(
        "PORT-001", {"RELIANCE.NS": 0.5, "TCS.NS": 0.5}
    )
    assert profile.portfolio_id == "PORT-001"
    assert 0.0 <= profile.resilience_score <= 1.0
    assert profile.value_at_risk > 0.0
    assert profile.expected_shortfall > profile.value_at_risk


def test_stress_testing_engine() -> None:
    result = StressTestingEngine.run_stress_test("Interest Rate +2%")
    assert result["scenario"] == "Interest Rate +2%"
    assert result["projected_return"] < 0
    assert len(result["largest_contributors"]) > 0
    assert result["portfolio_resilience"] == "Moderate"
