"""
==========================================================
TEST FORECAST DOMAIN MODELS
Module  : tests.forecast.test_models
Layer   : Tests / Domain
==========================================================
"""

from __future__ import annotations

import pytest
from dataclasses import FrozenInstanceError
from services.forecast.models import (
    ConfidenceLevel,
    ForecastAssumption,
    ForecastMethod,
    RevenueForecast,
    MarginForecast,
    CapexForecast,
    DepreciationForecast,
    WorkingCapitalForecast,
    TaxForecast,
    TerminalGrowthForecast,
    ForecastScenario,
)


def test_forecast_method_enum() -> None:
    assert ForecastMethod.CAGR.value == "cagr"
    assert ForecastMethod.LINEAR_REGRESSION.value == "linear_regression"


def test_confidence_level_enum() -> None:
    assert ConfidenceLevel.HIGH.value == "high"
    assert ConfidenceLevel.LOW.value == "low"


def test_forecast_assumption_model() -> None:
    assumption = ForecastAssumption(
        revenue_growth_rate=0.10,
        ebitda_margin=0.25,
        tax_rate=0.20,
        capex_pct_revenue=0.05,
        working_capital_pct_revenue=0.12,
    )
    assert assumption.revenue_growth_rate == 0.10

    # Test immutability
    with pytest.raises(FrozenInstanceError):
        assumption.revenue_growth_rate = 0.15  # type: ignore

    serialized = assumption.to_dict()
    assert serialized["ebitda_margin"] == 0.25


def test_revenue_forecast_model() -> None:
    rev = RevenueForecast(
        historical=(100.0, 110.0),
        projected=(121.0, 133.1),
        method=ForecastMethod.CAGR,
        confidence=ConfidenceLevel.HIGH,
        growth_rates=(0.10, 0.10),
    )
    assert rev.projected == (121.0, 133.1)
    assert rev.to_dict()["method"] == "cagr"
