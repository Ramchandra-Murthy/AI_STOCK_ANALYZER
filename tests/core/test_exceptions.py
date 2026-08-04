from __future__ import annotations

import pytest
from core.exceptions import (
    AIStockAnalyzerError,
    DomainError,
    ValidationError,
    InfrastructureError,
)

def test_exception_inheritance() -> None:
    assert issubclass(DomainError, AIStockAnalyzerError)
    assert issubclass(ValidationError, AIStockAnalyzerError)
    assert issubclass(InfrastructureError, AIStockAnalyzerError)

def test_raising_domain_error() -> None:
    with pytest.raises(DomainError, match="Business rule violated"):
        raise DomainError("Business rule violated")

def test_raising_validation_error() -> None:
    with pytest.raises(ValidationError, match="Invalid input"):
        raise ValidationError("Invalid input")

