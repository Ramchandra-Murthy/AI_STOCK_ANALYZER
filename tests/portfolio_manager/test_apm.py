from __future__ import annotations

from services.portfolio_manager.models import ManagedPortfolio
from services.portfolio_manager.portfolio_manager import ArtificialPortfolioManager


def test_managed_portfolio_immutability() -> None:
    mp = ManagedPortfolio(
        portfolio_id="MP-001",
        strategy="Core Quality",
        benchmark="Nifty 50",
        holdings=[{"symbol": "RELIANCE.NS", "weight": 1.0}],
        target_weights={"RELIANCE.NS": 1.0},
        cash_position=0.0,
        expected_return=0.16,
        expected_risk=0.14,
        expected_tracking_error=0.03,
        rebalance_required=False,
    )
    assert mp.portfolio_id == "MP-001"
    assert mp.cash_position == 0.0
    assert mp.timestamp is not None
    assert isinstance(mp.metadata, dict)


def test_artificial_portfolio_manager() -> None:
    portfolio = ArtificialPortfolioManager.construct_portfolio(
        "MP-002", "Institutional Growth", "Nifty 50"
    )
    assert portfolio.portfolio_id == "MP-002"
    assert len(portfolio.holdings) == 4
    assert sum(portfolio.target_weights.values()) <= 1.0

    is_valid = ArtificialPortfolioManager.validate_constraints(portfolio, 0.35)
    assert is_valid is True
