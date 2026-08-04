"""
==========================================================
FORECAST VALIDATION FRAMEWORK
Module  : services.forecast.validation
Layer   : Forecast Domain Validation
==========================================================
"""

from __future__ import annotations

from services.forecast.input import ForecastInput
from services.forecast.exceptions import ForecastValidationError


class ForecastValidator:
    """Enforces structural and mathematical domain validation rules for forecast execution inputs."""

    @staticmethod
    def validate_input(forecast_input: ForecastInput) -> None:
        """Validates historical continuity, horizon ranges, and boundary constraints."""
        if len(forecast_input.historical_years) < 2:
            raise ForecastValidationError(
                "At least 2 historical periods are required for trend-based forecasting."
            )

        # Verify chronological ordering of historical years
        years = forecast_input.historical_years
        if list(years) != sorted(years):
            raise ForecastValidationError(
                "Historical years must be in strictly chronological order."
            )

        # Verify forecast horizon does not overlap backward
        if forecast_input.forecast_years[0] <= years[-1]:
            raise ForecastValidationError(
                "Forecast horizon years must strictly succeed historical years."
            )

        # Validate margin bounds
        for idx, margin in enumerate(forecast_input.historical_margins):
            if not (0.0 <= margin <= 1.0):
                raise ForecastValidationError(
                    f"Historical margin at index {idx} ({margin}) is outside [0.0, 1.0]."
                )

        # Validate tax rate bounds
        for idx, tax in enumerate(forecast_input.historical_taxes):
            if not (0.0 <= tax <= 1.0):
                raise ForecastValidationError(
                    f"Historical tax rate at index {idx} ({tax}) is outside [0.0, 1.0]."
                )
