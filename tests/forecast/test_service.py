"""
==========================================================
TEST FORECAST ENGINE SERVICE ORCHESTRATOR
Module  : tests.forecast.test_service
Layer   : Tests / Forecast / Orchestration
==========================================================
"""

from __future__ import annotations

import pytest
from services.forecast.input import ForecastInput
from services.forecast.models import ForecastMethod
from services.forecast.result import ForecastResult
from services.forecast.service import ForecastService


def test_forecast_service_cagr_execution() -> None:
    inp = ForecastInput(
        symbol="INFY",
        historical_revenues=(1000.0, 1100.0, 1210.0),
        historical_ebits=(200.0, 220.0, 242.0),
        forecast_years=3,
        method=ForecastMethod.CAGR,
    )

    result = ForecastService.generate_forecast(inp)

    assert isinstance(result, ForecastResult)
    assert result.symbol == "INFY"
    assert result.forecast_horizon == 3
    assert result.method_used == ForecastMethod.CAGR
    assert len(result.revenue_forecast.projected) == 3
    assert len(result.ebit_forecast) == 3
    assert result.metadata["version"] == "5.1.0"


def test_forecast_service_guidance_execution() -> None:
    inp = ForecastInput(
        symbol="RELIANCE",
        historical_revenues=(5000.0, 5500.0),
        forecast_years=2,
        method=ForecastMethod.MANAGEMENT_GUIDANCE,
        management_guidance_revenue=(6000.0, 6800.0),
    )

    result = ForecastService.generate_forecast(inp)

    assert result.method_used == ForecastMethod.MANAGEMENT_GUIDANCE
    assert result.revenue_forecast.projected == (6000.0, 6800.0)
    assert result.revenue_forecast.guidance_override_applied is True
