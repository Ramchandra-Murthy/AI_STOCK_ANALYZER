from __future__ import annotations


class EROSError(Exception):
    """Base exception for all EROS platform errors."""

    pass


class ServiceError(EROSError):
    """Raised when an enterprise service encounters an execution failure."""

    pass


class RepositoryError(EROSError):
    """Raised when persistence operations fail."""

    pass


class ValidationError(EROSError):
    """Raised when input validation fails."""

    pass


class ValuationError(ServiceError):
    """Raised when financial valuation calculation fails."""

    pass


class ForecastError(ServiceError):
    """Raised when financial forecasting or scenario modeling fails."""

    pass


class PortfolioError(ServiceError):
    """Raised when portfolio optimization or risk evaluation fails."""

    pass


class ResearchError(ServiceError):
    """Raised when research orchestration or reasoning graph fails."""

    pass


class WorkflowError(ServiceError):
    """Raised when enterprise workflow execution fails."""

    pass
