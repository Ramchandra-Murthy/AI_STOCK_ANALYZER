from __future__ import annotations


class AIStockAnalyzerError(Exception):
    """Base exception for AI Stock Analyzer."""

    pass


class AIERPError(AIStockAnalyzerError):
    """ERP related error."""

    pass


class DomainError(AIERPError):
    """Domain layer error."""

    pass


class CalculationError(DomainError):
    """Calculation related error."""

    pass


class ValidationError(DomainError):
    """Validation error."""

    pass


class ValuationError(DomainError):
    """Valuation error."""

    pass


class SerializationError(AIERPError):
    """Serialization error."""

    pass


class PlatformError(AIERPError):
    """Platform level error."""

    pass


class RepositoryError(AIERPError):
    """Repository error."""

    pass


class InfrastructureError(AIERPError):
    """Infrastructure layer error."""

    pass
