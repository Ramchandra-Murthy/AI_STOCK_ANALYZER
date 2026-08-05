from __future__ import annotations
import pytest
from core.validation import validate_percentage
from core.exceptions import ValidationError

def test_finance_validation() -> None:
    validate_percentage(25.0, "rate")
    with pytest.raises(ValidationError):
        validate_percentage(150.0, "rate")
