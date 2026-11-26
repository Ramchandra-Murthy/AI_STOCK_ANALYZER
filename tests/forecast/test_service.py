"""
Module: tests.forecast.test_service
Description: Comprehensive unit tests for the ForecastService orchestrator.
Author: Engineering Team
Python Version: 3.13+
"""

from __future__ import annotations

import pytest

from services.forecast.exceptions import ForecastConfigurationError
from services.forecast.input import ForecastInput
from services.forecast.models import ConfidenceLevel, ForecastMethod
from services.forecast.service import ForecastService


def test_forecast_service_revenue() -> None:
    """Verify service correctly orchestrates revenue projections and growth rates."""
    service = ForecastService()
    historical = (100.0, 110.0, 121.0)

    rev_forecast = service.generate_revenue_forecast(
        historical=historical,
        periods=2,
        method=ForecastMethod.CAGR,
        confidence=ConfidenceLevel.HIGH,
    )

    assert rev_forecast.historical == historical
    assert len(rev_forecast.projected) == 2
    assert len(rev_forecast.growth_rates) == 2
    assert rev_forecast.method == ForecastMethod.CAGR
    assert rev_forecast.confidence == ConfidenceLevel.HIGH


def test_forecast_service_working_capital() -> None:
    """Verify service working capital delta calculations."""
    service = ForecastService()
    historical = (50.0, 60.0)

    wc_forecast = service.generate_working_capital_forecast(
        historical=historical,
        periods=2,
        method=ForecastMethod.LINEAR_REGRESSION,
    )

    assert len(wc_forecast.delta) == 2
    assert isinstance(wc_forecast.delta, tuple)


def test_forecast_service_scenario() -> None:
    """Verify end-to-end scenario bundling through the service layer."""
    service = ForecastService()

    scenario = service.generate_scenario(
        scenario_name="Base Case",
        probability=0.60,
        historical_revenue=(1000.0, 1100.0),
        historical_margin=(0.15, 0.16),
        historical_capex=(50.0, 55.0),
        periods=3,
        method=ForecastMethod.CAGR,
        historical_working_capital=(100.0, 110.0),
        historical_tax_rates=(0.24, 0.25),
    )

    assert scenario.scenario_name == "Base Case"
    assert scenario.probability == 0.60
    assert scenario.revenue_forecast is not None
    assert scenario.margin_forecast is not None
    assert scenario.capex_forecast is not None
    assert scenario.tax_forecast is not None
    assert scenario.terminal_growth is not None
    assert scenario.taxes.projected == pytest.approx((0.245, 0.245, 0.245))
    assert scenario.working_capital.projected == pytest.approx(
        tuple(value * 0.1 for value in scenario.revenue.projected)
    )
    assert scenario.assumptions.metadata["engine_version"] == "f10a-1"

    # Test round-trip dictionary serialization on the full scenario
    serialized = scenario.to_dict()
    reconstructed = scenario.from_dict(serialized)
    assert scenario == reconstructed


def test_forecast_service_scenario_preserves_legacy_callers() -> None:
    scenario = ForecastService().generate_scenario(
        scenario_name="Legacy Base Case",
        probability=0.5,
        historical_revenue=(1000.0, 1100.0),
        historical_margin=(0.15, 0.16),
        historical_capex=(50.0, 55.0),
        periods=2,
    )

    assert scenario.assumptions.metadata["compatibility_mode"] is True
    assert scenario.taxes.projected == pytest.approx((0.25, 0.25))


def test_forecast_service_selects_linear_regression() -> None:
    service = ForecastService()
    forecast = service.generate_revenue_forecast(
        historical=(10.0, 20.0, 30.0),
        periods=2,
        method=ForecastMethod.LINEAR_REGRESSION,
    )

    assert forecast.projected == pytest.approx((40.0, 50.0))
    assert forecast.method == ForecastMethod.LINEAR_REGRESSION


@pytest.mark.parametrize(
    "method",
    (
        ForecastMethod.ROLLING_AVERAGE,
        ForecastMethod.MANAGEMENT_GUIDANCE,
        ForecastMethod.HISTORICAL_MEAN,
    ),
)
def test_forecast_service_rejects_unsupported_methods(method: ForecastMethod) -> None:
    service = ForecastService()

    with pytest.raises(ForecastConfigurationError, match="not supported"):
        service.generate_revenue_forecast(
            historical=(100.0, 110.0, 121.0),
            periods=2,
            method=method,
        )


def test_execute_exposes_revenue_times_margin_as_ebit() -> None:
    forecast_input = ForecastInput(
        ticker="TCS",
        historical_years=(2023, 2024, 2025),
        historical_revenue=(100.0, 110.0, 121.0),
        historical_margins=(0.20, 0.21, 0.22),
        historical_capex=(5.0, 5.5, 6.0),
        historical_depreciation=(2.0, 2.2, 2.4),
        historical_working_capital=(10.0, 11.0, 12.0),
        historical_taxes=(0.25, 0.25, 0.25),
        forecast_years=(2026, 2027),
    )

    result = ForecastService().execute(forecast_input)

    assert result.status == "SUCCESS"
    assert result.package is not None
    expected_ebit = (121.0 * 1.1 * 0.22, 121.0 * 1.1 * 1.1 * 0.22)
    assert result.package.ebit.name == "EBIT"
    assert result.package.ebit.values == pytest.approx(expected_ebit)
    assert result.ebit_forecast == pytest.approx(expected_ebit)
    assert result.package.tax_rate.values == (0.25, 0.25)
    assert result.package.working_capital.values == pytest.approx(
        (13.2733333333, 14.6006666667)
    )
    assert result.metadata["assumption_engine"]["engine_version"] == "f10a-1"


def test_execute_uses_explicit_tax_rate_fallback_when_history_is_missing() -> None:
    forecast_input = ForecastInput(
        ticker="NO-TAX-HISTORY",
        historical_years=(2023, 2024),
        historical_revenue=(100.0, 110.0),
        historical_margins=(0.10, 0.11),
        historical_capex=(5.0, 5.5),
        historical_depreciation=(2.0, 2.2),
        historical_working_capital=(10.0, 11.0),
        historical_taxes=(),
        forecast_years=(2025,),
        tax_rate_assumption=0.22,
    )

    result = ForecastService().execute(forecast_input)

    assert result.status == "SUCCESS"
    assert result.package is not None
    assert result.package.tax_rate.values == pytest.approx((0.22,))
    assert result.metadata["assumption_engine"]["tax"]["method"] == "explicit_input_fallback"

