import pytest

from algorithmic_trading.position_sizing import (
    capped_quantity,
    fixed_fraction_size,
    fixed_risk_size,
    fractional_kelly_fraction,
    volatility_size,
)


def test_fixed_fraction_size() -> None:
    assert fixed_fraction_size(100_000, 0.10, 1_000) == 10


def test_fixed_risk_size() -> None:
    result = fixed_risk_size(100_000, 0.01, 1_000, 950)
    assert result.quantity == 20
    assert result.risk_budget == pytest.approx(1_000)
    assert result.risk_per_share == pytest.approx(50)


def test_volatility_size() -> None:
    result = volatility_size(100_000, 0.01, 0.02, 1_000)
    assert result.quantity == 50


def test_fractional_kelly_is_non_negative() -> None:
    assert fractional_kelly_fraction(0.60, 1.5, 0.25) == pytest.approx(0.0166666667)
    assert fractional_kelly_fraction(0.40, 1.0, 0.25) == 0.0


def test_quantity_cap() -> None:
    assert capped_quantity(100, 25) == 25
    assert capped_quantity(100) == 100
