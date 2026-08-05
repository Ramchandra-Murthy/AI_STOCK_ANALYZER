from __future__ import annotations


class ForecastError(Exception):
    """Base exception for all forecast-related errors."""

    pass


class ForecastValidationError(ForecastError):
    """Raised when forecast input data fails validation checks."""

    pass


class ForecastAlgorithmError(ForecastError):
    """Raised when a forecasting algorithm encounters a calculation failure."""

    pass


class ForecastConfigurationError(ForecastError):
    """Raised when the forecast service is incorrectly configured."""

    pass


class ForecastSerializationError(ForecastError):
    """Raised when serialization or deserialization of forecast data fails."""

    pass
