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
    assert result.package.working_capital.values == pytest.approx((13.2733333333, 14.6006666667))
    assert result.metadata["assumption_engine"]["engine_version"] == "f10a-6"


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


def test_scenario_uses_historical_working_capital_with_explicit_tax_fallback() -> None:
    scenario = ForecastService().generate_scenario(
        scenario_name="Historical WC / Explicit Tax",
        probability=0.5,
        historical_revenue=(100.0, 110.0),
        historical_margin=(0.15, 0.16),
        historical_capex=(5.0, 5.5),
        periods=2,
        historical_working_capital=(10.0, 22.0),
        tax_rate_assumption=0.23,
    )

    assert scenario.assumptions.working_capital_pct_revenue == pytest.approx(0.15)
    assert scenario.assumptions.tax_rate == pytest.approx(0.23)
    assert scenario.assumptions.metadata["working_capital"]["method"] == (
        "historical_nwc_to_revenue"
    )
    assert scenario.assumptions.metadata["tax"]["method"] == "explicit_input_fallback"


def test_scenario_uses_historical_tax_with_explicit_working_capital_fallback() -> None:
    scenario = ForecastService().generate_scenario(
        scenario_name="Historical Tax / Explicit WC",
        probability=0.5,
        historical_revenue=(100.0, 110.0),
        historical_margin=(0.15, 0.16),
        historical_capex=(5.0, 5.5),
        periods=2,
        historical_tax_rates=(0.20, 0.24),
        working_capital_pct_revenue_assumption=0.12,
    )

    assert scenario.assumptions.tax_rate == pytest.approx(0.22)
    assert scenario.assumptions.working_capital_pct_revenue == pytest.approx(0.12)
    assert scenario.assumptions.metadata["working_capital"]["method"] == ("explicit_input_fallback")
    assert scenario.assumptions.metadata["tax"]["method"] == "historical_effective_tax_rate"


def test_scenario_rejects_missing_working_capital_source_without_legacy_fallback() -> None:
    with pytest.raises(ValueError, match="historical_nwc or an explicit"):
        ForecastService().generate_scenario(
            scenario_name="Missing WC Source",
            probability=0.5,
            historical_revenue=(100.0, 110.0),
            historical_margin=(0.15, 0.16),
            historical_capex=(5.0, 5.5),
            periods=2,
            historical_tax_rates=(0.20, 0.24),
        )


def test_scenario_rejects_missing_tax_source_without_legacy_fallback() -> None:
    with pytest.raises(ValueError, match="historical tax rates"):
        ForecastService().generate_scenario(
            scenario_name="Missing Tax Source",
            probability=0.5,
            historical_revenue=(100.0, 110.0),
            historical_margin=(0.15, 0.16),
            historical_capex=(5.0, 5.5),
            periods=2,
            historical_working_capital=(10.0, 11.0),
        )


def test_scenario_supports_both_explicit_assumption_fallbacks() -> None:
    scenario = ForecastService().generate_scenario(
        scenario_name="Explicit Assumptions",
        probability=0.5,
        historical_revenue=(100.0, 110.0),
        historical_margin=(0.15, 0.16),
        historical_capex=(5.0, 5.5),
        periods=2,
        tax_rate_assumption=0.22,
        working_capital_pct_revenue_assumption=0.13,
    )

    assert scenario.assumptions.tax_rate == pytest.approx(0.22)
    assert scenario.assumptions.working_capital_pct_revenue == pytest.approx(0.13)
    assert scenario.assumptions.metadata["tax"]["fallback_used"] is True
    assert scenario.assumptions.metadata["working_capital"]["fallback_used"] is True


def test_scenario_partial_inputs_do_not_silently_use_legacy_defaults() -> None:
    with pytest.raises(ValueError, match="historical_nwc or an explicit"):
        ForecastService().generate_scenario(
            scenario_name="Partial Inputs",
            probability=0.5,
            historical_revenue=(100.0, 110.0),
            historical_margin=(0.15, 0.16),
            historical_capex=(5.0, 5.5),
            periods=2,
            historical_tax_rates=(0.20, 0.24),
        )


def test_execute_all_five_assumptions_drive_canonical_projection_lines() -> None:
    forecast_input = ForecastInput(
        ticker="ASSUMPTIONS",
        historical_years=(2023, 2024, 2025),
        historical_revenue=(100.0, 110.0, 121.0),
        historical_margins=(0.10, 0.11, 0.12),
        historical_capex=(-5.0, -5.5, -6.0),
        historical_depreciation=(2.0, 2.2, 2.4),
        historical_working_capital=(-10.0, -11.0, -12.0),
        historical_taxes=(0.20, 0.21, 0.22),
        forecast_years=(2026, 2027),
        custom_growth_rate=0.05,
        ebit_margin_assumption=0.18,
        capex_pct_revenue_assumption=0.07,
        working_capital_pct_revenue_assumption=-0.08,
    )
    result = ForecastService().execute(forecast_input)

    assert result.status == "SUCCESS"
    assert result.package is not None
    projected_revenue = (121.0 * 1.05, 121.0 * 1.05**2)
    assert result.package.revenue.values == pytest.approx(projected_revenue)
    assert result.package.ebit.values == pytest.approx(
        tuple(value * 0.18 for value in projected_revenue)
    )
    assert result.package.capex.values == pytest.approx(
        tuple(value * 0.07 for value in projected_revenue)
    )
    assert result.package.working_capital.values == pytest.approx(
        tuple(value * -0.08 for value in projected_revenue)
    )
    assert result.package.tax_rate.values == pytest.approx((0.21, 0.21))
    provenance = result.metadata["assumption_engine"]["provenance"]
    assert provenance["revenue_growth"]["method"] == "explicit_input"
    assert provenance["ebit_margin"]["method"] == "explicit_input"
    assert provenance["capex_pct_revenue"]["method"] == "explicit_input"
    assert provenance["working_capital_pct_revenue"]["method"] == "explicit_input"
    assert provenance["tax_rate"]["method"] == "historical_effective_tax_rate"


def test_execute_management_guidance_overrides_explicit_revenue_and_margin() -> None:
    from services.forecast.assumption_engine import ManagementGuidance

    forecast_input = ForecastInput(
        ticker="GUIDANCE",
        historical_years=(2023, 2024),
        historical_revenue=(100.0, 110.0),
        historical_margins=(0.10, 0.11),
        historical_capex=(5.0, 5.5),
        historical_depreciation=(2.0, 2.2),
        historical_working_capital=(10.0, 11.0),
        historical_taxes=(0.20, 0.21),
        forecast_years=(2025,),
        custom_growth_rate=0.03,
        ebit_margin_assumption=0.15,
        management_guidance=ManagementGuidance(
            revenue_cagr_override=0.12,
            target_ebit_margin_override=0.25,
            source="approved management plan",
            reason="board-approved forecast",
        ),
    )
    result = ForecastService().execute(forecast_input)

    assert result.status == "SUCCESS"
    assert result.package is not None
    assert result.package.revenue.values == pytest.approx((110.0 * 1.12,))
    assert result.package.ebit.values == pytest.approx((110.0 * 1.12 * 0.25,))
    assert (
        result.metadata["assumption_engine"]["provenance"]["revenue_growth"]["method"]
        == "management_override"
    )


def test_execute_linear_regression_uses_slope_over_latest_revenue() -> None:
    from services.forecast.algorithms.linear_regression import LinearRegressionForecastEngine

    forecast_input = ForecastInput(
        ticker="REGRESSION",
        historical_years=(2023, 2024, 2025),
        historical_revenue=(100.0, 120.0, 140.0),
        historical_margins=(0.10, 0.11, 0.12),
        historical_capex=(5.0, 6.0, 7.0),
        historical_depreciation=(2.0, 2.2, 2.4),
        historical_working_capital=(10.0, 12.0, 14.0),
        historical_taxes=(0.20, 0.21, 0.22),
        forecast_years=(2026,),
    )
    result = ForecastService(LinearRegressionForecastEngine()).execute(forecast_input)

    assert result.status == "SUCCESS"
    assert result.package is not None
    # Regression slope is 20; scalar growth is 20 / latest revenue (140).
    assert result.package.revenue.values == pytest.approx((140.0 * (1.0 + 20.0 / 140.0),))
    assert (
        result.metadata["assumption_engine"]["provenance"]["revenue_growth"]["method"]
        == "linear_regression_slope_over_latest_revenue"
    )


def test_execute_rejects_management_override_without_provenance() -> None:
    from services.forecast.assumption_engine import ManagementGuidance

    forecast_input = ForecastInput(
        ticker="INVALID-GUIDANCE",
        historical_years=(2023, 2024),
        historical_revenue=(100.0, 110.0),
        historical_margins=(0.10, 0.11),
        historical_capex=(5.0, 5.5),
        historical_depreciation=(2.0, 2.2),
        historical_working_capital=(10.0, 11.0),
        historical_taxes=(0.20, 0.21),
        forecast_years=(2025,),
        management_guidance=ManagementGuidance(revenue_cagr_override=0.1),
    )
    result = ForecastService().execute(forecast_input)
    assert result.status == "FAILED"
    assert "source and reason" in (result.error_message or "")


def test_forecast_assumption_ebit_margin_serialization_is_backward_compatible() -> None:
    from services.forecast.models import ForecastAssumption

    assumption = ForecastAssumption(
        revenue_growth_rate=0.10,
        ebitda_margin=0.18,
        tax_rate=0.22,
        capex_pct_revenue=0.05,
        working_capital_pct_revenue=-0.08,
    )
    serialized = assumption.to_dict()
    assert assumption.ebit_margin == pytest.approx(0.18)
    assert serialized["ebit_margin"] == pytest.approx(0.18)
    assert ForecastAssumption.from_dict(serialized) == assumption

    legacy_payload = dict(serialized)
    legacy_payload.pop("ebit_margin")
    assert ForecastAssumption.from_dict(legacy_payload) == assumption


def test_execute_allows_negative_historical_and_projected_ebit_margin() -> None:
    forecast_input = ForecastInput(
        ticker="NEGATIVE-EBIT",
        historical_years=(2024, 2025),
        historical_revenue=(100.0, 90.0),
        historical_margins=(-0.05, -0.10),
        historical_capex=(5.0, 4.5),
        historical_depreciation=(2.0, 2.0),
        historical_working_capital=(10.0, 9.0),
        historical_taxes=(0.0, 0.0),
        forecast_years=(2026,),
    )
    result = ForecastService().execute(forecast_input)
    assert result.status == "SUCCESS"
    assert result.package is not None
    assert result.package.ebit.values == pytest.approx((-8.1,))


@pytest.mark.parametrize("nwc_ratio", (0.12, -0.08))
def test_execute_uses_explicit_working_capital_ratio_without_history(nwc_ratio: float) -> None:
    forecast_input = ForecastInput(
        ticker="NO-NWC-HISTORY",
        historical_years=(2024, 2025),
        historical_revenue=(100.0, 110.0),
        historical_margins=(0.10, 0.11),
        historical_capex=(5.0, 5.5),
        historical_depreciation=(2.0, 2.2),
        historical_working_capital=(),
        historical_taxes=(0.20, 0.21),
        forecast_years=(2026, 2027),
        working_capital_pct_revenue_assumption=nwc_ratio,
    )

    result = ForecastService().execute(forecast_input)

    assert result.status == "SUCCESS"
    assert result.package is not None
    projected_revenue = (121.0, 133.1)
    assert result.package.working_capital.values == pytest.approx(
        tuple(value * nwc_ratio for value in projected_revenue)
    )
    assert (
        result.metadata["assumption_engine"]["provenance"]["working_capital_pct_revenue"]["method"]
        == "explicit_input"
    )


def test_execute_rejects_missing_nwc_history_without_explicit_ratio() -> None:
    forecast_input = ForecastInput(
        ticker="MISSING-NWC-SOURCE",
        historical_years=(2024, 2025),
        historical_revenue=(100.0, 110.0),
        historical_margins=(0.10, 0.11),
        historical_capex=(5.0, 5.5),
        historical_depreciation=(2.0, 2.2),
        historical_working_capital=(),
        historical_taxes=(0.20, 0.21),
        forecast_years=(2026,),
    )

    result = ForecastService().execute(forecast_input)

    assert result.status == "FAILED"
    assert "working_capital_pct_revenue_assumption is required" in (result.error_message or "")


def test_execute_rejects_misaligned_nonempty_nwc_even_with_explicit_ratio() -> None:
    forecast_input = ForecastInput(
        ticker="MISALIGNED-NWC",
        historical_years=(2024, 2025),
        historical_revenue=(100.0, 110.0),
        historical_margins=(0.10, 0.11),
        historical_capex=(5.0, 5.5),
        historical_depreciation=(2.0, 2.2),
        historical_working_capital=(10.0,),
        historical_taxes=(0.20, 0.21),
        forecast_years=(2026,),
        working_capital_pct_revenue_assumption=0.12,
    )

    result = ForecastService().execute(forecast_input)

    assert result.status == "FAILED"
    assert "historical_working_capital length" in (result.error_message or "")



@pytest.mark.parametrize("nwc_ratio", (float("nan"), float("inf"), float("-inf")))
def test_execute_rejects_nonfinite_explicit_nwc_ratio_without_history(nwc_ratio: float) -> None:
    forecast_input = ForecastInput(
        ticker="NONFINITE-NWC-RATIO",
        historical_years=(2024, 2025),
        historical_revenue=(100.0, 110.0),
        historical_margins=(0.10, 0.11),
        historical_capex=(5.0, 5.5),
        historical_depreciation=(2.0, 2.2),
        historical_working_capital=(),
        historical_taxes=(0.20, 0.21),
        forecast_years=(2026,),
        working_capital_pct_revenue_assumption=nwc_ratio,
    )

    result = ForecastService().execute(forecast_input)

    assert result.status == "FAILED"
    assert "working_capital_pct_revenue_assumption must be a finite number" in (
        result.error_message or ""
    )
