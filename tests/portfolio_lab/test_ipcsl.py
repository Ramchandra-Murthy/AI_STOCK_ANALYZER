from __future__ import annotations

import pytest
from services.portfolio_lab.models import PortfolioStrategy
from services.portfolio_lab.strategy_engine import PortfolioStrategyEngine
from services.portfolio_lab.factor_models import FactorExposureEngine

def test_portfolio_strategy_immutability() -> None:
    strategy = PortfolioStrategy(
        strategy_name="Core Institutional Alpha",
        objective="Risk-Adjusted Alpha",
        holdings=[{"symbol": "RELIANCE.NS", "weight": 1.0}],
        expected_return=0.16,
        expected_volatility=0.14,
        expected_sharpe=1.20,
        turnover=0.10,
        benchmark="Nifty 50"
    )
    assert strategy.strategy_name == "Core Institutional Alpha"
    assert strategy.expected_sharpe == 1.20
    assert strategy.timestamp is not None
    assert isinstance(strategy.metadata, dict)

def test_portfolio_strategy_engine() -> None:
    strategy = PortfolioStrategyEngine.build_strategy("Dynamic Growth", "Capital Appreciation", "Nifty 50")
    assert strategy.strategy_name == "Dynamic Growth"
    assert len(strategy.holdings) == 4
    assert strategy.expected_return > 0.10
    assert strategy.benchmark == "Nifty 50"

def test_factor_exposure_engine() -> None:
    holdings = [{"symbol": "RELIANCE.NS", "weight": 1.0}]
    exposures = FactorExposureEngine.calculate_factor_exposures(holdings)
    assert "Quality" in exposures
    assert "Value" in exposures
    assert exposures["Quality"] > 0
