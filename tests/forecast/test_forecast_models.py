"""
==========================================================
TEST FORECAST DOMAIN MODELS
Module  : tests.forecast.test_forecast_models
Layer   : Tests / Forecast / Domain Models
==========================================================
"""

from __future__ import annotations

import dataclasses
import pytest
from services.forecast.forecast_models import (
    ConfidenceLevel,
    ForecastAssumption,
    ForecastConfidence,
    ForecastMethod,
    ForecastProtocol,
    ForecastScenario,
    ForecastSeries,
    MarginForecast,
    RevenueForecast,
    TerminalGrowthForecast,
)


def test_forecast_method_enum() -> None:
    assert ForecastMethod.CAGR == "cagr"
    assert ForecastMethod.HISTORICAL_MEAN == "historical_mean"
    assert list(ForecastMethod) == [
        ForecastMethod.CAGR,
        ForecastMethod.HISTORICAL_MEAN,
        ForecastMethod.LINEAR_REGRESSION,
        ForecastMethod.EXPONENTIAL_SMOOTHING,
        ForecastMethod.MANAGEMENT_GUIDANCE,
    ]


def test_confidence_level_enum() -> None:
    assert ConfidenceLevel.HIGH == "high"
    assert ConfidenceLevel.UNCERTAIN == "uncertain"


def test_forecast_assumption_immutability_and_serialization() -> None:
    assumption = ForecastAssumption(
        name="Growth Rate",
        value=0.08,
        description="Historical average",
        source="Annual Report",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        assumption.value = 0.10  # type: ignore[misc]

    data = assumption.to_dict()
    assert data["name"] == "Growth Rate"
    assert data["value"] == 0.08
    assert data["source"] == "Annual Report"


def test_revenue_forecast_protocol_and_inheritance() -> None:
    rev_forecast = RevenueForecast(
        historical=(100.0, 110.0),
        projected=(121.0, 133.1),
        method=ForecastMethod.CAGR,
        confidence=ConfidenceLevel.HIGH,
        growth_rates=(0.10, 0.10),
    )

    # Verify structural protocol compliance
    assert isinstance(rev_forecast, ForecastProtocol)

    # Verify field synchronization / behavior
    assert rev_forecast.projected == (121.0, 133.1)
    assert rev_forecast.projected_revenue == (121.0, 133.1)

    # Round-trip serialization check
    serialized = rev_forecast.to_dict()
    assert serialized["historical"] == [100.0, 110.0]
    assert serialized["projected"] == [121.0, 133.1]
    assert serialized["method"] == "cagr"


def test_margin_forecast_sync() -> None:
    margin_fc = MarginForecast(
        historical=(0.20, 0.22),
        projected=(0.25,),
        margins=(0.25,),
    )
    assert margin_fc.margins == (0.25,)
    assert margin_fc.projected_margins == (0.25,)


def test_forecast_scenario_serialization() -> None:
    scenario = ForecastScenario(
        scenario_name="Bull",
        probability=0.25,
        revenue_multiplier=1.2,
        margin_expansion_bps=50.0,
    )
    data = scenario.to_dict()
    assert data["scenario_name"] == "Bull"
    assert data["probability"] == 0.25
    assert data["margin_expansion_bps"] == 50.0
