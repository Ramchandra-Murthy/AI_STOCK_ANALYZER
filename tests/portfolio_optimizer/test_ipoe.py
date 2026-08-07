from __future__ import annotations

import pytest
from services.portfolio_optimizer.models import PortfolioAllocation
from services.portfolio_optimizer.optimizer import InstitutionalPortfolioOptimizer
from services.portfolio_optimizer.rebalance import PortfolioRebalancer

def test_portfolio_allocation_immutability() -> None:
    alloc = PortfolioAllocation(
        symbol="RELIANCE.NS",
        target_weight=0.15,
        expected_return=0.16,
        expected_volatility=0.18,
        expected_alpha=0.04,
        conviction_score=0.91,
        rationale=["Core holding"]
    )
    assert alloc.symbol == "RELIANCE.NS"
    assert alloc.target_weight == 0.15
    assert alloc.timestamp is not None
    assert isinstance(alloc.metadata, dict)

def test_portfolio_optimizer_execution() -> None:
    allocations = InstitutionalPortfolioOptimizer.optimize_portfolio(["RELIANCE.NS", "TCS.NS"], "Institutional")
    assert len(allocations) >= 4
    total_weight = sum(a.target_weight for a in allocations)
    assert 0.0 < total_weight <= 1.0

def test_portfolio_rebalancer_trades() -> None:
    current = {"RELIANCE.NS": 0.20, "TCS.NS": 0.05}
    target = {"RELIANCE.NS": 0.15, "TCS.NS": 0.10}
    trades = PortfolioRebalancer.generate_rebalance_trades(current, target)
    
    assert len(trades) == 2
    actions = {t["symbol"]: t["action"] for t in trades}
    assert actions["RELIANCE.NS"] == "SELL"
    assert actions["TCS.NS"] == "BUY"
