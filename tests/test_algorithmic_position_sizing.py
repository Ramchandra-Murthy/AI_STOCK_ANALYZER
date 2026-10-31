import pytest

from algorithmic_trading.position_sizing import fixed_risk_size


def test_fixed_risk_quantity_respects_risk_budget() -> None:
    result = fixed_risk_size(100_000, 0.01, 500, 450)

    assert result.quantity == 20
    assert result.risk_budget == pytest.approx(1_000)
    assert result.quantity * result.risk_per_share <= result.risk_budget


def test_fixed_risk_quantity_is_capped_by_available_capital() -> None:
    # A very tight stop would otherwise size above the cash available.
    result = fixed_risk_size(10_000, 0.01, 9_000, 8_999)

    assert result.quantity == 1
    assert result.quantity * 9_000 <= 10_000


@pytest.mark.parametrize(
    ("capital", "risk_fraction", "entry", "stop"),
    [
        (0, 0.01, 100, 95),
        (1_000, 0, 100, 95),
        (1_000, 0.01, 0, 95),
        (1_000, 0.01, 100, 100),
        (1_000, 0.01, float("nan"), 95),
        (1_000, 0.01, 100, float("inf")),
    ],
)
def test_fixed_risk_returns_zero_for_invalid_inputs(
    capital: float,
    risk_fraction: float,
    entry: float,
    stop: float,
) -> None:
    result = fixed_risk_size(capital, risk_fraction, entry, stop)

    assert result.quantity == 0
