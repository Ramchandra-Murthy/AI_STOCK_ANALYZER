from __future__ import annotations

from dataclasses import dataclass
from core.exceptions import ValidationError

@dataclass(frozen=True, slots=True)
class Percentage:
    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.value, (int, float)):
            raise ValidationError(f"Percentage value must numeric, got {type(self.value)}")

    @classmethod
    def from_rate(cls, rate: float) -> Percentage:
        return cls(rate)

    @classmethod
    def from_basis_points(cls, bps: float) -> Percentage:
        return cls(bps / 10000.0)

    @property
    def as_rate(self) -> float:
        return self.value

    @property
    def as_basis_points(self) -> float:
        return self.value * 10000.0

    @property
    def as_percentage(self) -> float:
        return self.value * 100.0
