from __future__ import annotations

import logging
import random
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class MonteCarloEngine:
    """Generates probabilistic Monte Carlo paths and tail-risk outcome distributions."""

    @staticmethod
    def run_simulation_paths(num_paths: int = 1000, expected_return: float = 0.12, volatility: float = 0.15, horizon_years: float = 1.0) -> Dict[str, Any]:
        logger.info("Executing %d Monte Carlo simulation paths over %.1f years", num_paths, horizon_years)

        terminal_returns = []
        for _ in range(num_paths):
            # Sample normal distribution approximation for path return
            path_return = random.gauss(expected_return * horizon_years, volatility * (horizon_years ** 0.5))
            terminal_returns.append(path_return)

        terminal_returns.sort()
        median_return = terminal_returns[num_paths // 2]
        positive_count = sum(1 for r in terminal_returns if r > 0)
        prob_positive = round(positive_count / num_paths, 4)
        
        loss_10_count = sum(1 for r in terminal_returns if r < -0.10)
        prob_loss_10 = round(loss_10_count / num_paths, 4)

        return {
            "num_paths": num_paths,
            "median_return": round(median_return, 4),
            "probability_positive_return": prob_positive,
            "probability_loss_greater_10pct": prob_loss_10,
            "expected_shortfall_tail": round(terminal_returns[int(num_paths * 0.05)], 4) # 5th percentile tail
        }
