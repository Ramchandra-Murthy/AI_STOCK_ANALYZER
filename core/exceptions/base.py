from __future__ import annotations

class AIStockAnalyzerError(Exception):
    """Base exception for all domain and infrastructure errors in the platform."""
    pass

class DomainError(AIStockAnalyzerError):
    """Raised when a business rule or invariant is violated within a domain."""
    pass

class ValidationError(AIStockAnalyzerError):
    """Raised when input data, types, or constraints fail validation."""
    pass

class InfrastructureError(AIStockAnalyzerError):
    """Raised when an external system, database, or provider fails."""
    pass

