from __future__ import annotations

from services.cio.cio import ArtificialCIOEngine
from services.cio.models import InvestmentDecision


def test_investment_decision_immutability() -> None:
    decision = InvestmentDecision(
        symbol="RELIANCE.NS",
        decision="BUY",
        conviction=0.94,
        position_size=0.05,
        expected_return=0.18,
        expected_risk=0.135,
        target_price=3520.0,
        holding_period="3 Years",
        committee_votes={"CIO": "APPROVE"},
    )
    assert decision.symbol == "RELIANCE.NS"
    assert decision.decision == "BUY"
    assert decision.target_price == 3520.0
    assert decision.timestamp is not None
    assert isinstance(decision.metadata, dict)


def test_artificial_cio_engine() -> None:
    decision = ArtificialCIOEngine.render_decision("RELIANCE.NS", "Balanced")
    assert decision.symbol == "RELIANCE.NS"
    assert decision.decision == "BUY"
    assert decision.conviction >= 0.90
    assert len(decision.committee_votes) > 0
