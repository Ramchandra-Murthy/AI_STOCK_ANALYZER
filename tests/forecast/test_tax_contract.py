from __future__ import annotations

import pytest

from services.forecast.algorithms.cagr import CAGRForecastEngine
from services.forecast.algorithms.linear_regression import LinearRegressionForecastEngine
from services.forecast.exceptions import ForecastConfigurationError
from services.forecast.forecast_input import ForecastInput as LegacyForecastInput
from services.forecast.forecast_models import (
    CapexForecast, ConfidenceLevel, DepreciationForecast, ForecastConfidence,
    MarginForecast, RevenueForecast, TaxForecast, TerminalGrowthForecast,
    WorkingCapitalForecast,
)
from services.forecast.forecast_result import ForecastResult
from services.forecast.input import ForecastInput


@pytest.mark.parametrize("algorithm", [CAGRForecastEngine(), LinearRegressionForecastEngine()])
def test_canonical_tax_algorithms_require_explicit_assumption_when_history_missing(algorithm):
    inp = ForecastInput(
        ticker="NO-TAX-HISTORY", historical_years=(2023, 2024),
        historical_revenue=(100.0, 110.0), historical_margins=(0.10, 0.11),
        historical_capex=(5.0, 5.5), historical_depreciation=(2.0, 2.2),
        historical_working_capital=(10.0, 11.0), historical_taxes=(),
        forecast_years=(2025,),
    )
    with pytest.raises(ForecastConfigurationError, match="tax_rate_assumption"):
        algorithm.calculate_taxes(inp)


def test_legacy_tax_rate_excludes_nonpositive_pbt_periods():
    from services.forecast.tax_forecast import TaxForecastEngine
    inp = LegacyForecastInput(
        symbol="MATCHED-HISTORY", historical_revenues=(100.0, 110.0, 120.0),
        historical_pbt=(100.0, 0.0, -20.0), historical_tax=(20.0, 0.0, 5.0),
        forecast_years=1,
    )
    result = TaxForecastEngine().forecast_tax(inp)
    assert result.projected == pytest.approx((0.20,))
    assert result.historical == pytest.approx((0.20,))


def test_nopat_and_fcff_convert_tax_rate_to_tax_expense():
    confidence = ConfidenceLevel.HIGH
    result = ForecastResult(
        symbol="TAX-TEST", revenue=RevenueForecast(projected=(1000.0,)),
        margin=MarginForecast(projected=(0.10,)), capex=CapexForecast(projected=(5.0,)),
        depreciation=DepreciationForecast(projected=(10.0,)),
        working_capital=WorkingCapitalForecast(projected=(5.0,)),
        tax=TaxForecast(projected=(0.25,)),
        terminal_growth=TerminalGrowthForecast(0.03, confidence),
        confidence=ForecastConfidence(90.0, confidence),
    )
    assert result.projected_tax_expense == pytest.approx((25.0,))
    assert result.projected_nopat == pytest.approx((75.0,))
    assert result.projected_fcff == pytest.approx((75.0,))
    yearly = result.yearly_forecasts[0]
    assert yearly.tax_rate == pytest.approx(0.25)
    assert yearly.tax_expense == pytest.approx(25.0)
    assert yearly.free_cash_flow == pytest.approx(75.0)
