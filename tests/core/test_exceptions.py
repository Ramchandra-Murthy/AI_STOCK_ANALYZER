from __future__ import annotations

import pytest
from core.exceptions import (
    AIERPError,
    ValidationError,
    SerializationError,
    ForecastError,
    ValuationError,
    MarketDataError,
    ResearchError,
)

def test_exception_inheritance() -> None:
    assert issubclass(ValidationError, AIERPError)
    assert issubclass(SerializationError, AIERPError)
    assert issubclass(ForecastError, AIERPError)
    assert issubclass(ValuationError, AIERPError)
    assert issubclass(MarketDataError, AIERPError)
    assert issubclass(ResearchError, AIERPError)

def test_raising_base_error() -> None:
    with pytest.raises(AIERPError):
        raise ForecastError("Model convergence failed")
