from __future__ import annotations

import pytest
from core.types import Currency, Money, Percentage, FiscalPeriod
from core.exceptions import ValidationError

def test_currency_validation() -> None:
    curr = Currency("inr")
    assert curr.code == "INR"
    with pytest.raises(ValidationError):
        Currency("invalid")

def test_money_operations() -> None:
    m1 = Money(100.50, "INR")
    m2 = Money(50.25, "INR")
    m3 = m1 + m2
    assert float(m3.amount) == 150.75
    assert str(m3.currency) == "INR"

    with pytest.raises(ValidationError):
        _ = m1 + Money(10.0, "USD")

def test_percentage_conversions() -> None:
    p = Percentage.from_rate(0.125)
    assert p.as_rate == 0.125
    assert p.as_percentage == 12.5
    assert p.as_basis_points == 1250.0

    p_bps = Percentage.from_basis_points(150.0)
    assert p_bps.as_rate == 0.015

def test_fiscal_period() -> None:
    fp_year = FiscalPeriod(2026)
    assert str(fp_year) == "FY2026"

    fp_qtr = FiscalPeriod(2026, 2)
    assert str(fp_qtr) == "FY2026-Q2"

    with pytest.raises(ValidationError):
        FiscalPeriod(1800)
    with pytest.raises(ValidationError):
        FiscalPeriod(2026, 5)
