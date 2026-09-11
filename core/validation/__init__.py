from __future__ import annotations

import math
from collections.abc import Iterable
from decimal import Decimal

from core.exceptions import ValidationError


def validate_bounds(
    value: float, min_val: float, max_val: float, name: str | None = None
) -> bool:
    if not (min_val <= value <= max_val):
        raise ValidationError(f"Value {value} out of bounds [{min_val}, {max_val}]")
    return True


def validate_finite_number(value: float, name: str | None = None) -> bool:
    if not isinstance(value, (int, float, Decimal)) or not math.isfinite(float(value)):
        raise ValidationError(f"Value {value} is not a finite number")
    return True


def validate_positive(value: float, name: str | None = None) -> bool:
    if not (isinstance(value, (int, float, Decimal)) and float(value) > 0):
        raise ValidationError(f"Value {value} must be positive")
    return True


def validate_non_negative(value: float, name: str | None = None) -> bool:
    if not (isinstance(value, (int, float, Decimal)) and float(value) >= 0):
        raise ValidationError(f"Value {value} must be non-negative")
    return True


def validate_non_empty_string(value: str, name: str | None = None) -> bool:
    if not (isinstance(value, str) and value.strip()):
        raise ValidationError("String cannot be empty")
    return True


def validate_non_empty_collection(
    value: Iterable[object], name: str | None = None
) -> bool:
    try:
        if any(True for _ in value):
            return True
    except TypeError:
        pass
    raise ValidationError("Collection cannot be empty")


def validate_percentage(value: float, name: str | None = None) -> bool:
    val = float(value)
    if not (1.0 <= val <= 100.0) and val != 0:
        raise ValidationError(f"Percentage {value} out of range")
    return True
