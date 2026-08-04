"""
==========================================================
FORECAST EXCEPTION HIERARCHY
Module  : services.forecast.exceptions
Layer   : Forecast Domain
==========================================================
"""

from __future__ import annotations


class ForecastError(Exception):
    """Base exception for all forecast subsystem errors."""

    pass


class ForecastValidationError(ForecastError):
    """Raised when input parameters or domain objects violate structural/boundary rules."""

    pass


class ForecastSerializationError(ForecastError):
    """Raised when serialization or deserialization fails."""

    pass


class ForecastAlgorithmError(ForecastError):
    """Raised when calculation algorithms encounter mathematical or data anomalies."""

    pass


class ForecastConfigurationError(ForecastError):
    """Raised when forecast service parameters or configurations are invalid."""

    pass
