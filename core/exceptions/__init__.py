from __future__ import annotations


class AIStockAnalyzerError(Exception):
    """Base exception for AI Stock Analyzer."""


class AIERPError(AIStockAnalyzerError):
    """ERP related error."""


class DomainError(AIERPError):
    """Domain layer error."""


class CalculationError(DomainError):
    """Calculation related error."""


class ValidationError(DomainError):
    """Validation error."""


class ValuationError(DomainError):
    """Valuation error."""


class SerializationError(AIERPError):
    """Serialization error."""


class PlatformError(AIERPError):
    """Platform level error."""


class RepositoryError(AIERPError):
    """Repository error."""


class InfrastructureError(AIERPError):
    """Infrastructure layer error."""
