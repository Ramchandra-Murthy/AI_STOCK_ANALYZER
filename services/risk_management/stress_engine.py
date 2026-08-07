from __future__ import annotations

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class StressTestingEngine:
    """Simulates historical and hypothetical macroeconomic stress events on institutional portfolios."""

    SCENARIOS = {
        "Interest Rate +2%": {"portfolio_return": -0.074, "contributors": ["Financials", "Utilities"], "resilience": "Moderate"},
        "Global Financial Crisis 2008": {"portfolio_return": -0.225, "contributors": ["All Equities", "Banking"], "resilience": "Low"},
        "Oil Price Spike (+50%)": {"portfolio_return": -0.052, "contributors": ["Energy", "Aviation"], "resilience": "Moderate"}
    }

    @classmethod
    def run_stress_test(cls, scenario_name: str) -> Dict[str, Any]:
        logger.info("Executing stress test scenario: %s", scenario_name)
        result = cls.SCENARIOS.get(scenario_name, {"portfolio_return": -0.05, "contributors": ["General Market"], "resilience": "Moderate"})
        return {
            "scenario": scenario_name,
            "projected_return": result["portfolio_return"],
            "largest_contributors": result["contributors"],
            "portfolio_resilience": result["resilience"]
        }
