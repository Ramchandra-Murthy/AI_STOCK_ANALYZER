from __future__ import annotations

import pytest
from core.validation import (
    validate_finite_number,
    validate_bounds,
    validate_positive,
    validate_percentage,
    validate_non_empty_string,
    validate_non_empty_collection,
)
from core.exceptions import ValidationError

def test_number_validation() -> None:
    validate_finite_number(10.5, "test_num")
    with pytest.raises(ValidationError):
        validate_finite_number(float("nan"), "test_num")

    validate_bounds(5, 1, 10, "range_num")
    with pytest.raises(ValidationError):
        validate_bounds(15, 1, 10, "range_num")

    validate_positive(100, "pos_num")
    with pytest.raises(ValidationError):
        validate_positive(-5, "pos_num")

def test_finance_validation() -> None:
    validate_percentage(0.25, "rate")
    with pytest.raises(ValidationError):
        validate_percentage(1.5, "rate")

def test_string_and_collection_validation() -> None:
    validate_non_empty_string("Bandra", "city")
    with pytest.raises(ValidationError):
        validate_non_empty_string("   ", "city")

    validate_non_empty_collection([1, 2, 3], "items")
    with pytest.raises(ValidationError):
        validate_non_empty_collection([], "items")
