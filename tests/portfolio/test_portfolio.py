from __future__ import annotations

import pytest
from services.portfolio.engine import PortfolioAnalyticsEngine


def test_portfolio_analytics_evaluation() -> None:
    holdings = {
        "RELIANCE.NS": {"shares": 500.0, "price": 1400.0, "cost_basis": 1250.0},
        "TCS.NS": {"shares": 200.0, "price": 3800.0, "cost_basis": 3500.0},
    }

    engine = PortfolioAnalyticsEngine()
    result = engine.analyze(holdings)

    assert result.total_portfolio_value > 0.0
    assert len(result.positions) == 2
    assert result.sharpe_ratio > 0.0
    assert result.monte_carlo_median_end_value > 0.0
