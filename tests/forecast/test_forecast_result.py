"""Regression tests for the structured forecast result contract."""

import pytest

from services.forecast.exceptions import ForecastValidationError
from services.forecast.forecast_models import (
    CapexForecast,
    ConfidenceLevel,
    DepreciationForecast,
    ForecastConfidence,
    ForecastMethod,
    MarginForecast,
    RevenueForecast,
    TaxForecast,
    TerminalGrowthForecast,
    WorkingCapitalForecast,
)
from services.forecast.forecast_result import ForecastResult


def _forecast_result(*, margin_years=(2026, 2027, 2028)) -> ForecastResult:
    years = (2026, 2027, 2028)
    return ForecastResult(
        symbol="TEST",
        revenue=RevenueForecast(values=(100.0, 110.0, 121.0), years=years),
        margin=MarginForecast(values=(0.2, 0.21, 0.22), years=margin_years),
        capex=CapexForecast(values=(10.0, 11.0, 12.0), years=years),
        depreciation=DepreciationForecast(values=(4.0, 4.5, 5.0), years=years),
        working_capital=WorkingCapitalForecast(values=(20.0, 22.0, 24.0), years=years),
        tax=TaxForecast(values=(0.25, 0.25, 0.25), years=years),
        terminal_growth=TerminalGrowthForecast(0.03, ConfidenceLevel.MEDIUM),
        confidence=ForecastConfidence(80.0, ConfidenceLevel.HIGH),
        scenarios=(),
        metadata={"method": ForecastMethod.CAGR.value},
    )


def test_yearly_forecasts_preserve_calendar_years() -> None:
    result = _forecast_result()

    assert tuple(item.year for item in result.yearly_forecasts) == (2026, 2027, 2028)


def test_yearly_forecasts_reject_misaligned_series_years() -> None:
    result = _forecast_result(margin_years=(2025, 2026, 2027))

    with pytest.raises(ForecastValidationError, match="margin forecast years"):
        _ = result.yearly_forecasts
