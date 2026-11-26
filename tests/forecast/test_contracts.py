from __future__ import annotations

from dataclasses import replace

import pytest

from services.forecast.exceptions import ForecastValidationError
from services.forecast.input import ForecastInput
from services.forecast.validation import ForecastValidator


@pytest.fixture
def valid_forecast_input() -> ForecastInput:
    return ForecastInput(
        ticker="INFY",
        historical_years=(2023, 2024, 2025),
        historical_revenue=(100.0, 110.0, 121.0),
        historical_margins=(0.20, 0.22, 0.25),
        historical_capex=(8.0, 9.0, 10.0),
        historical_depreciation=(4.0, 4.5, 5.0),
        historical_working_capital=(15.0, 16.0, 18.0),
        historical_taxes=(0.25, 0.25, 0.25),
        forecast_years=(2026, 2027),
    )


def test_validator_passes_valid_input(valid_forecast_input: ForecastInput) -> None:
    ForecastValidator.validate_input(valid_forecast_input)


def test_validator_fails_empty_ticker(valid_forecast_input: ForecastInput) -> None:
    bad_input = replace(valid_forecast_input, ticker="")
    with pytest.raises(ForecastValidationError):
        ForecastValidator.validate_input(bad_input)


def test_validator_fails_length_mismatch(valid_forecast_input: ForecastInput) -> None:
    bad_input = replace(valid_forecast_input, historical_revenue=(100.0, 110.0))
    with pytest.raises(ForecastValidationError, match="historical_revenue length"):
        ForecastValidator.validate_input(bad_input)


@pytest.mark.parametrize("years", [(2023, 2023, 2024), (2024, 2023, 2025)])
def test_validator_rejects_duplicate_or_unordered_historical_years(
    valid_forecast_input: ForecastInput, years: tuple[int, ...]
) -> None:
    bad_input = replace(valid_forecast_input, historical_years=years)
    with pytest.raises(ForecastValidationError, match="historical_years"):
        ForecastValidator.validate_input(bad_input)


def test_validator_rejects_gaps_in_historical_years(
    valid_forecast_input: ForecastInput,
) -> None:
    bad_input = replace(valid_forecast_input, historical_years=(2022, 2024, 2025))
    with pytest.raises(ForecastValidationError, match="consecutive annual"):
        ForecastValidator.validate_input(bad_input)


@pytest.mark.parametrize("years", [(2026, 2026), (2027, 2026)])
def test_validator_rejects_duplicate_or_unordered_forecast_years(
    valid_forecast_input: ForecastInput, years: tuple[int, ...]
) -> None:
    bad_input = replace(valid_forecast_input, forecast_years=years)
    with pytest.raises(ForecastValidationError, match="forecast_years"):
        ForecastValidator.validate_input(bad_input)


def test_validator_rejects_gaps_in_forecast_years(
    valid_forecast_input: ForecastInput,
) -> None:
    bad_input = replace(valid_forecast_input, forecast_years=(2026, 2028))
    with pytest.raises(ForecastValidationError, match="consecutive annual"):
        ForecastValidator.validate_input(bad_input)


@pytest.mark.parametrize("years", [(2025, 2026), (2027, 2028)])
def test_validator_requires_forecast_to_start_immediately_after_history(
    valid_forecast_input: ForecastInput, years: tuple[int, ...]
) -> None:
    bad_input = replace(valid_forecast_input, forecast_years=years)
    with pytest.raises(ForecastValidationError, match="forecast_years must"):
        ForecastValidator.validate_input(bad_input)
