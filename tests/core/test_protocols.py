from __future__ import annotations

import pytest
from typing import Any
from core.protocols import Serializable, Validatable

class DummyRecord:
    def __init__(self, value: float) -> None:
        self.value = value

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value}

    def validate(self) -> None:
        if self.value < 0:
            raise ValueError("Value cannot be negative")

def test_protocols() -> None:
    record = DummyRecord(42.0)
    
    assert isinstance(record, Serializable)
    assert isinstance(record, Validatable)
    
    assert record.to_dict() == {"value": 42.0}
    record.validate()
