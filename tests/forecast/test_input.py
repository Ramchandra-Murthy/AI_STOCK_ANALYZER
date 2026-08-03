"""
==========================================================
TEST FORECAST INPUT DOMAIN & VALIDATION
Module  : tests.forecast.test_input
Layer   : Tests / Forecast / Input DTOs
==========================================================
"""

from __future__ import annotations

import pytest
from services.forecast.exceptions import ValuationError
from services.forecast.input import ForecastInput
from services.forecast.models import ForecastMethod, HistoricalFinancials


def test_forecast_input_valid_flat() -> None:
    inp = ForecastInput(
        symbol="AAPL",
        historical_revenues=(100.0, 110.0, 120.0),
        historical_ebits=(20.0, 22.0, 25.0),
        forecast_years=3,
        method=ForecastMethod.CAGR,
    )
    assert inp.symbol == "AAPL"
    assert inp.historical_revenues == (100.0, 110.0, 120.0)
    assert inp.forecast_horizon == 3
    assert inp.forecast_years == 3
    assert inp.historical_data is not None
    assert inp.historical_data.revenue == (100.0, 110.0, 120.0)


def test_forecast_input_valid_nested() -> None:
    historical = HistoricalFinancials(revenue=(500.0, 550.0))
    inp = ForecastInput(
        symbol="GOOG",
        historical_data=historical,
        forecast_horizon=5,
    )
    assert inp.symbol == "GOOG"
    assert inp.historical_revenues == (500.0, 550.0)
    assert inp.forecast_horizon == 5


def test_forecast_input_empty_symbol_raises() -> None:
    with pytest.raises(ValuationError, match="Ticker symbol cannot be empty"):
        ForecastInput(symbol="   ", historical_revenues=(100.0, 110.0))


def test_forecast_input_insufficient_history_raises() -> None:
    with pytest.raises(
        ValuationError, match="Historical revenues must contain at least 2 periods"
    ):
        ForecastInput(symbol="MSFT", historical_revenues=(100.0,))


def test_forecast_input_invalid_horizon_raises() -> None:
    with pytest.raises(ValuationError, match="Forecast horizon"):
        ForecastInput(
            symbol="AMZN", historical_revenues=(100.0, 110.0), forecast_years=15
        )


def test_forecast_input_ebits_length_mismatch_raises() -> None:
    with pytest.raises(ValuationError, match="historical_ebits length"):
        ForecastInput(
            symbol="META",
            historical_revenues=(100.0, 110.0),
            historical_ebits=(20.0,),
        )


def test_forecast_input_guidance_length_mismatch_raises() -> None:
    with pytest.raises(ValuationError, match="management_guidance_revenue length"):
        ForecastInput(
            symbol="NFLX",
            historical_revenues=(100.0, 110.0),
            forecast_years=3,
            management_guidance_revenue=(120.0, 130.0),  # expects 3 values
        )
