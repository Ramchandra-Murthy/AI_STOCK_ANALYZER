from __future__ import annotations

import pytest
from decimal import Decimal
from core.types import Money

def test_money_creation_and_precision() -> None:
    m = Money(Decimal("1000.50"), "INR")
    assert m.amount == Decimal("1000.50")
    assert m.currency == "INR"

def test_money_arithmetic() -> None:
    m1 = Money(Decimal("500.00"), "INR")
    m2 = Money(Decimal("250.50"), "INR")
    
    res_add = m1 + m2
    assert res_add.amount == Decimal("750.50")
    assert res_add.currency == "INR"

    res_sub = m1 - m2
    assert res_sub.amount == Decimal("249.50")

def test_money_currency_mismatch() -> None:
    m_inr = Money(Decimal("100"), "INR")
    m_usd = Money(Decimal("100"), "USD")
    
    with pytest.raises(ValueError, match="Cannot add different currencies"):
        _ = m_inr + m_usd
