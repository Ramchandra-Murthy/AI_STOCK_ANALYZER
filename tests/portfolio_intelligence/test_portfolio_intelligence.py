from __future__ import annotations

from services.portfolio_intelligence.models import Portfolio, Position
from services.portfolio_intelligence.service import PortfolioIntelligenceService


def test_portfolio_intelligence_layer() -> None:
    pos1 = Position(
        symbol="RELIANCE.NS",
        quantity=100.0,
        average_cost=2400.0,
        current_price=2800.0,
        sector="Energy & Retail",
        industry="Conglomerate",
        expected_return=0.16,
        expected_risk=0.18,
        intrinsic_value=3200.0,
        committee_signal="BUY",
    )
    pos2 = Position(
        symbol="TCS.NS",
        quantity=50.0,
        average_cost=3500.0,
        current_price=3900.0,
        sector="Technology",
        industry="IT Services",
        expected_return=0.12,
        expected_risk=0.15,
        intrinsic_value=4100.0,
        committee_signal="HOLD",
    )

    portfolio = Portfolio(
        portfolio_id="PORT-001", owner="Ramchandra Murthy", cash=50000.0, positions=[pos1, pos2]
    )

    sector_alloc = PortfolioIntelligenceService.compute_sector_allocation(portfolio)
    assert "Energy & Retail" in sector_alloc
    assert "Technology" in sector_alloc
    assert "CASH" in sector_alloc

    decision = PortfolioIntelligenceService.evaluate_portfolio(portfolio)
    assert decision.portfolio_id == "PORT-001"
    assert decision.expected_return > 0.0
    assert len(decision.recommended_actions) == 2
    assert decision.portfolio_score > 50.0
    assert "Portfolio evaluation complete" in decision.rebalance_summary
