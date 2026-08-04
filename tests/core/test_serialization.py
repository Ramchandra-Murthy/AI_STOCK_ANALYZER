from __future__ import annotations

import pytest
from datetime import date
from decimal import Decimal
from core.serialization import to_json, from_json

def test_json_serialization() -> None:
    data = {
        "amount": Decimal("150.50"),
        "date": date(2026, 4, 15),
        "description": "Bandra Office Rent"
    }
    
    json_str = to_json(data)
    assert isinstance(json_str, str)
    assert "150.5" in json_str
    assert "2026-04-15" in json_str

    deserialized = from_json(json_str)
    assert deserialized["amount"] == 150.5
    assert deserialized["date"] == "2026-04-15"
    assert deserialized["description"] == "Bandra Office Rent"
