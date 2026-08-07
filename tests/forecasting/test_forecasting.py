from __future__ import annotations

import pytest
from services.forecasting.models import ForecastScenario
from services.forecasting.scenario_engine import ScenarioIntelligenceEngine

def test_forecasting_and_scenario_engine() -> None:
    scenarios = [
        ForecastScenario(
            scenario_id="SCEN-001",
            name="BULL",
            probability=0.25,
            revenue_growth=0.15,
            margin=0.21,
            wacc=0.095,
            terminal_growth=0.045,
            inflation=0.04,
            interest_rate=0.065,
            intrinsic_value=3450.0,
            expected_return=0.22,
            risk_score=0.30
        ),
        ForecastScenario(
            scenario_id="SCEN-002",
            name="BASE",
            probability=0.50,
            revenue_growth=0.10,
            margin=0.18,
            wacc=0.10,
            terminal_growth=0.04,
            inflation=0.05,
            interest_rate=0.07,
            intrinsic_value=2900.0,
            expected_return=0.15,
            risk_score=0.45
        ),
        ForecastScenario(
            scenario_id="SCEN-003",
            name="BEAR",
            probability=0.25,
            revenue_growth=0.04,
            margin=0.14,
            wacc=0.115,
            terminal_growth=0.03,
            inflation=0.07,
            interest_rate=0.085,
            intrinsic_value=2100.0,
            expected_return=0.02,
            risk_score=0.70
        )
    ]

    result = ScenarioIntelligenceEngine.evaluate_scenarios("RELIANCE.NS", scenarios)
    
    assert result.symbol == "RELIANCE.NS"
    assert result.expected_value > 0.0
    assert result.bull_value == 3450.0
    assert result.base_value == 2900.0
    assert result.bear_value == 2100.0
    assert result.confidence > 0.80
    assert len(result.probability_distribution) == 3
