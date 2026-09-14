from __future__ import annotations

from .base import (
    AIERPError,
    CalculationError,
    DomainError,
    InfrastructureError,
    SerializationError,
    ValidationError,
)
from .forecast import ForecastError
from .valuation import ValuationError

AIStockAnalyzerError = AIERPError

__all__ = [
    "AIStockAnalyzerError",
    "AIERPError",
    "DomainError",
    "CalculationError",
    "ValidationError",
    "ValuationError",
    "SerializationError",
    "InfrastructureError",
    "ForecastError",
]
