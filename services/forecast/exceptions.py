"""
==========================================================
FORECAST EXCEPTION HIERARCHY
Module  : services.forecast.exceptions
Layer   : Domain / Forecast
==========================================================
"""

from __future__ import annotations


class ForecastError(Exception):
    """Base exception for all forecast-related errors."""

    pass


class ForecastValidationError(ForecastError):
    """Raised when data structures fail structural or boundary validation."""

    pass


class ForecastSerializationError(ForecastError):
    """Raised when serialization or deserialization of domain objects fails."""

    pass


class ForecastConfigurationError(ForecastError):
    """Raised when forecast engine configuration is invalid or inconsistent."""

    pass
