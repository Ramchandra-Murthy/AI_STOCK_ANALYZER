from __future__ import annotations

"""
==========================================================
CUSTOM DOMAIN EXCEPTIONS
Module  : core.exceptions
Version : 4.0.0
==========================================================
"""

from typing import Any

class PlatformError(Exception):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

class ValidationError(PlatformError):
    def __init__(self, message: str, discrepancies: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=discrepancies)

class ParserError(PlatformError):
    pass

class RepositoryError(PlatformError):
    pass

class ValuationError(PlatformError):
    pass

class ForecastError(PlatformError):
    pass

class DispatcherError(PlatformError):
    pass

class ReportGenerationError(PlatformError):
    pass

class ConfigurationError(PlatformError):
    pass
