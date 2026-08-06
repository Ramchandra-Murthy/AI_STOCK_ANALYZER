import math
from core.exceptions import ValidationError

class StringValidators:
    @staticmethod
    def not_empty(value: str, field_name: str = "Field") -> str:
        if not value or not str(value).strip():
            raise ValidationError(f"{field_name} cannot be empty.")
        return str(value)

    @staticmethod
    def non_empty(value: str, field_name: str = "Field") -> str:
        return StringValidators.not_empty(value, field_name)

class NumericValidators:
    @staticmethod
    def positive(value: float, field_name: str = "Value") -> float:
        if value <= 0:
            raise ValidationError(f"{field_name} must be positive, got {value}.")
        return float(value)

    @staticmethod
    def non_negative(value: float, field_name: str = "Value") -> float:
        if value < 0:
            raise ValidationError(f"{field_name} cannot be negative, got {value}.")
        return float(value)

def validate_non_empty_string(value: str, field_name: str = "Field") -> str:
    return StringValidators.not_empty(value, field_name)

def validate_bounds(value: float, lower: float, upper: float, field_name: str = "Value") -> float:
    if not (lower <= value <= upper):
        raise ValidationError(f"{field_name} {value} is out of bounds [{lower}, {upper}].")
    return float(value)

def validate_percentage(value: float, field_name: str = "Percentage") -> float:
    return validate_bounds(value, 0.0, 100.0, field_name)

def validate_finite_number(value: float, field_name: str = "Number") -> float:
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValidationError(f"{field_name} must be a finite number.")
    return float(value)
