"""
EXAMPLE: BASIC FORECAST PACKAGE USAGE
Module: services.forecast.examples.basic_forecast
"""

from __future__ import annotations

from services.forecast.models import (
    ForecastMethod,
    ConfidenceLevel,
    ForecastFrequency,
    ScenarioType,
    ForecastMetadata,
    RevenueForecast,
    MarginForecast,
    CapexForecast,
    DepreciationForecast,
    WorkingCapitalForecast,
    TaxForecast,
    TerminalGrowthForecast,
    ForecastConfidence,
    ForecastAssumption,
    ForecastScenario,
    ForecastPackage,
)


def main() -> None:
    print("Initializing Enterprise Forecast Package...")

    metadata = ForecastMetadata(
        created_at="2026-08-04",
        author="Institutional Research Division",
        version="v5.1.0-alpha.1",
        description="Base case and stress testing projections.",
    )

    scenario = ForecastScenario(
        scenario_type=ScenarioType.BASE,
        method=ForecastMethod.CAGR,
        revenue=RevenueForecast(
            values=(10000.0, 11000.0, 12100.0),
            years=(2026, 2027, 2028),
            frequency=ForecastFrequency.ANNUAL,
        ),
        margins=MarginForecast(values=(0.25, 0.26, 0.27), years=(2026, 2027, 2028)),
        capex=CapexForecast(values=(500.0, 550.0, 600.0), years=(2026, 2027, 2028)),
        depreciation=DepreciationForecast(
            values=(200.0, 220.0, 240.0), years=(2026, 2027, 2028)
        ),
        working_capital=WorkingCapitalForecast(
            values=(1000.0, 1100.0, 1210.0), years=(2026, 2027, 2028)
        ),
        taxes=TaxForecast(values=(0.25, 0.25, 0.25), years=(2026, 2027, 2028)),
        terminal_growth=TerminalGrowthForecast(
            rate=0.03, confidence=ConfidenceLevel.HIGH
        ),
        confidence=ForecastConfidence(score=95.0, level=ConfidenceLevel.HIGH),
        assumptions=ForecastAssumption(
            revenue_growth_rate=0.10,
            ebitda_margin=0.25,
            tax_rate=0.25,
            capex_pct_revenue=0.05,
            working_capital_pct_revenue=0.10,
            metadata={"source": "consensus"},
        ),
        scenario_name="Base Growth",
    )

    package = ForecastPackage(ticker="TCS.NS", scenarios=(scenario,), metadata=metadata)

    # Verification
    serialized = package.to_dict()
    restored = ForecastPackage.from_dict(serialized)

    print(f"Ticker         : {package.ticker}")
    print(f"Scenarios Count: {len(package.scenarios)}")
    print(f"Revenue Stream : {package.scenarios[0].revenue.values}")
    print(f"Round-Trip OK  : {package == restored}")


if __name__ == "__main__":
    main()
