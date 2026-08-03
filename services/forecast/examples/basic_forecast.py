```python
"""
Module: services.forecast.examples.basic_forecast
Description: Executable reference demonstrating domain model instantiation and serialization.
Author: Engineering Team
Python Version: 3.13+
"""

from __future__ import annotations

import json
from services.forecast.models import (
    ConfidenceLevel,
    ForecastAssumption,
    ForecastMethod,
    ForecastScenario,
    RevenueForecast,
    TerminalGrowthForecast,
)


def run_example() -> None:
    """Demonstrates building a complete forecast scenario payload."""
    print("Initializing Financial Forecasting Models...")

    # 1. Revenue projection series
    revenue_model = RevenueForecast(
        historical=(100_000.0, 112_000.0, 125_000.0),
        projected=(140_000.0, 156_800.0),
        growth_rates=(0.12, 0.12),
        method=ForecastMethod.CAGR,
        confidence=ConfidenceLevel.HIGH,
    )

    # 2. Terminal growth assumption
    terminal_growth = TerminalGrowthForecast(
        terminal_growth_rate=0.03,
        method=ForecastMethod.CAGR,
        confidence=ConfidenceLevel.MEDIUM,
    )

    # 3. Qualitative assumptions
    assumption = ForecastAssumption(
        parameter_name="market_expansion",
        value=0.15,
        rationale="Growth driven by international tier-2 city expansion.",
    )

    # 4. Aggregate scenario container
    scenario = ForecastScenario(
        scenario_name="Base Case",
        revenue_forecast=revenue_model,
        terminal_growth=terminal_growth,
        probability=0.70,
        assumptions=(assumption,),
    )

    # 5. Export to JSON payload
    payload = scenario.to_dict()
    pretty_json = json.dumps(payload, indent=2)

    print("\nSuccessfully serialized forecast scenario:")
    print(pretty_json)


if __name__ == "__main__":
    run_example()