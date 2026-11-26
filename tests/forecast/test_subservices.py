"""
==========================================================
EQUITY VALUATION PLATFORM v5.1
Module  : tests.forecast.test_subservices
==========================================================
"""

import pytest

from services.forecast.capex_forecast import CapExForecastEngine
from services.forecast.depreciation_forecast import DepreciationForecastEngine
from services.forecast.exceptions import ForecastConfigurationError
from services.forecast.margin_forecast import MarginForecastEngine
from services.forecast.revenue_forecast import RevenueForecastEngine
from services.forecast.forecast_input import ForecastInput
from services.forecast.forecast_models import ForecastMethod
from services.forecast.tax_forecast import TaxForecastEngine
from services.forecast.working_capital_forecast import WorkingCapitalForecastEngine


@pytest.fixture
def base_input() -> ForecastInput:
    return ForecastInput(
        symbol="TCS.NS",
        historical_revenues=(100.0, 110.0, 120.0),
        forecast_years=2,
        historical_ebits=(20.0, 22.0, 24.0),
        historical_capex=(5.0, 5.5, 6.0),
        historical_depreciation=(2.0, 2.2, 2.4),
        historical_nwc=(10.0, 11.0, 12.0),
        method=ForecastMethod.CAGR,
    )


def test_capex_and_depreciation_engines(base_input: ForecastInput):
    capex_engine = CapExForecastEngine()
    dep_engine = DepreciationForecastEngine()

    projected_revs = (130.0, 140.0)

    capex_res = capex_engine.forecast_capex(base_input, projected_revs)
    dep_res = dep_engine.forecast_depreciation(base_input, projected_revs)

    assert len(capex_res.projected) == 2
    assert len(dep_res.projected) == 2


def test_working_capital_delta_calculation(base_input: ForecastInput):
    nwc_engine = WorkingCapitalForecastEngine()
    projected_revs = (130.0, 140.0)

    res = nwc_engine.forecast_working_capital(base_input, projected_revenues=projected_revs)
    assert len(res.projected_nwc) == 2


def test_tax_forecast_engine(base_input: ForecastInput) -> None:
    tax_engine = TaxForecastEngine()
    res = tax_engine.forecast_tax(base_input)
    assert res is not None
    assert len(res.projected) == base_input.forecast_years


def test_legacy_revenue_engine_dispatches_supported_algorithms(base_input: ForecastInput) -> None:
    engine = RevenueForecastEngine()
    expected = {
        ForecastMethod.CAGR: (120.0 * (1.2**0.5), 144.0),
        ForecastMethod.LINEAR_REGRESSION: (130.0, 140.0),
        ForecastMethod.ROLLING_AVERAGE: (110.0, 110.0),
    }
    for method, values in expected.items():
        result = engine.forecast_revenue(base_input, method=method)
        assert result.projected == pytest.approx(values)
        assert result.method == method


def test_legacy_revenue_engine_applies_management_guidance(base_input: ForecastInput) -> None:
    guided_input = ForecastInput(
        symbol=base_input.symbol,
        historical_revenues=base_input.historical_revenues,
        forecast_years=2,
        management_guidance_revenue=(135.0, 150.0),
    )
    result = RevenueForecastEngine().forecast_revenue(
        guided_input, method=ForecastMethod.MANAGEMENT_GUIDANCE
    )
    assert result.projected == (135.0, 150.0)
    assert result.method == ForecastMethod.MANAGEMENT_GUIDANCE


def test_legacy_margin_engine_supports_historical_mean_and_mean_reversion(
    base_input: ForecastInput,
) -> None:
    engine = MarginForecastEngine()
    historical_mean = engine.forecast_margins(
        base_input, method=ForecastMethod.HISTORICAL_MEAN
    )
    mean_reversion = engine.forecast_margins(
        base_input, method=ForecastMethod.MEAN_REVERSION
    )
    assert historical_mean.projected == pytest.approx((0.2, 0.2))
    assert historical_mean.method == ForecastMethod.HISTORICAL_MEAN
    assert len(mean_reversion.projected) == base_input.forecast_years
    assert mean_reversion.method == ForecastMethod.MEAN_REVERSION


def test_legacy_margin_engine_rejects_unrelated_methods(base_input: ForecastInput) -> None:
    with pytest.raises(ForecastConfigurationError, match="not supported"):
        MarginForecastEngine().forecast_margins(
            base_input, method=ForecastMethod.LINEAR_REGRESSION
        )



def test_tax_forecast_defaults_to_manual_method(base_input: ForecastInput) -> None:
    result = TaxForecastEngine().forecast_tax(base_input)
    assert result.method == ForecastMethod.MANUAL
