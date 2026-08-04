from __future__ import annotations

from dataclasses import dataclass
from core.exceptions import ValidationError

@dataclass(frozen=True, slots=True)
class Currency:
    code: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or len(self.code.strip()) != 3:
            raise ValidationError(f"Invalid currency code: {self.code}. Must be a 3-letter ISO string.")
        object.__setattr__(self, "code", self.code.upper().strip())

    def __str__(self) -> str:
        return self.code
