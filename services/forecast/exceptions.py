from __future__ import annotations

class ForecastError(Exception):
    pass

class ForecastValidationError(ForecastError):
    pass

class ForecastAlgorithmError(ForecastError):
    pass

class ForecastConfigurationError(ForecastError):
    pass

class ForecastSerializationError(ForecastError):
    pass
