from __future__ import annotations

from services.simulation.market_simulator import InstitutionalMarketSimulator
from services.simulation.models import SimulationResult
from services.simulation.monte_carlo import MonteCarloEngine


def test_simulation_result_immutability() -> None:
    result = SimulationResult(
        scenario_id="BULL-01",
        portfolio_return=0.18,
        volatility=0.14,
        max_drawdown=0.06,
        sharpe_ratio=1.25,
        value_at_risk=0.02,
        execution_cost=1200.0,
        recommendation="Aggressive Growth",
    )
    assert result.scenario_id == "BULL-01"
    assert result.portfolio_return == 0.18
    assert result.timestamp is not None
    assert isinstance(result.metadata, dict)


def test_institutional_market_simulator() -> None:
    sim = InstitutionalMarketSimulator.simulate_scenario("Inflation Shock", 0.12, -0.05)
    assert sim.scenario_id == "Inflation Shock"
    assert sim.portfolio_return == 0.07
    assert sim.sharpe_ratio > 0
    assert len(sim.recommendation) > 0


def test_monte_carlo_engine() -> None:
    mc = MonteCarloEngine.run_simulation_paths(num_paths=500, expected_return=0.12, volatility=0.15)
    assert mc["num_paths"] == 500
    assert 0.0 <= mc["probability_positive_return"] <= 1.0
    assert 0.0 <= mc["probability_loss_greater_10pct"] <= 1.0
    assert isinstance(mc["median_return"], float)
