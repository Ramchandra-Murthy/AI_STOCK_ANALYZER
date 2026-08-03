"""
==========================================================
TEST FORECAST ENGINE VALIDATION CONTRACTS
Module  : tests.forecast.test_validation
Layer   : Tests / Forecast / Domain Validation
==========================================================
"""

from __future__ import annotations

import pytest
from services.forecast.exceptions import ValuationError
from services.forecast.input import ForecastInput
from services.forecast.validation import ForecastValidator


def test_validator_passes_valid_input() -> None:
    inp = ForecastInput(
        symbol="TCS",
        historical_revenues=(1000.0, 1100.0, 1200.0),
        historical_ebits=(200.0, 220.0, 240.0),
        forecast_years=3,
    )
    # Should not raise any exception
    ForecastValidator.validate_input(inp)


def test_validator_fails_non_positive_revenue() -> None:
    inp = ForecastInput(
        symbol="BAD_REV",
        historical_revenues=(1000.0, 0.0, 1200.0),
    )
    with pytest.raises(ValuationError, match="strictly positive"):
        ForecastValidator.validate_input(inp)


def test_validator_fails_invalid_growth_rate_bounds() -> None:
    with pytest.raises(ValuationError, match="violates institutional bounds"):
        ForecastValidator.validate_growth_rates((0.05, 6.5, 0.04))


def test_validator_passes_valid_growth_rates() -> None:
    # Should not raise
    ForecastValidator.validate_growth_rates((0.05, 0.12, -0.02))
