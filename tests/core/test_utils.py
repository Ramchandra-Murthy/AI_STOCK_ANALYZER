from __future__ import annotations

import pytest
from decimal import Decimal
from core.utils import round_currency, format_currency

def test_rounding() -> None:
    assert round_currency(150.565, 2) == Decimal("150.57")
    assert round_currency(150.564, 2) == Decimal("150.56")

def test_formatting() -> None:
    assert format_currency(125000.5, "₹") == "₹125,000.50"
