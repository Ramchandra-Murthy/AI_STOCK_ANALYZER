from __future__ import annotations


class AIERPError(Exception):
    """Base exception for all AI Institutional Equity Research Platform errors."""

    pass


class DomainError(AIERPError):
    """Base exception for business logic and domain validation errors."""

    pass


class CalculationError(DomainError):
    """Raised when a financial or quantitative calculation fails (e.g. division by zero, invalid convergence)."""

    pass


class ValidationError(DomainError):
    """Raised when input parameters fail strict business rule validation."""

    pass


class SerializationError(AIERPError):
    """Raised when data serialization or deserialization fails."""

    pass


class InfrastructureError(AIERPError):
    """Raised when external data sources, database connectors, or APIs fail."""

    pass
