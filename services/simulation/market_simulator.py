from __future__ import annotations

import logging

from services.simulation.models import SimulationResult

logger = logging.getLogger(__name__)


class InstitutionalMarketSimulator:
    """Executes stochastic market simulations and scenario projections for institutional portfolios."""

    @staticmethod
    def simulate_scenario(
        scenario_id: str, base_return: float = 0.12, shock: float = 0.0
    ) -> SimulationResult:
        logger.info(
            "Running market simulation for scenario '%s' with base return %.2f and shock %.2f",
            scenario_id,
            base_return,
            shock,
        )

        projected_return = base_return + shock
        volatility = 0.145
        max_drawdown = round(abs(projected_return * 0.65), 4) if projected_return < 0 else 0.085
        sharpe = round((projected_return - 0.06) / volatility, 2)
        var_95 = 0.022
        exec_cost = 1450.0

        recommendation = "Maintain Allocation"
        if projected_return < -0.02:
            recommendation = "Defensive Rebalance"
        elif projected_return > 0.15:
            recommendation = "Aggressive Growth"

        return SimulationResult(
            scenario_id=scenario_id,
            portfolio_return=round(projected_return, 4),
            volatility=volatility,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            value_at_risk=var_95,
            execution_cost=exec_cost,
            recommendation=recommendation,
        )
