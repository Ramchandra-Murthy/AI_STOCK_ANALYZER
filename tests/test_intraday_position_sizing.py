"""Tests for intraday position sizing."""

from services.intraday_position_sizing import calculate_position_size


def test_long_position_size_is_capped_by_risk_and_capital():
    result = calculate_position_size(100000, 100, 100, 98, 104, "LONG")
    assert result.risk_amount == 500
    assert result.risk_quantity == 250
    assert result.capital_quantity == 100
    assert result.quantity == 100
    assert result.planned_risk == 200
    assert result.planned_reward == 400
    assert result.planned_rr == 2


def test_short_position_size_and_reward():
    result = calculate_position_size(50000, 2, 200, 205, 190, "SHORT")
    assert result.risk_amount == 200
    assert result.quantity == 40
    assert result.planned_risk == 200
    assert result.planned_reward == 400
    assert result.planned_rr == 2


def test_position_size_never_exceeds_initial_capital_or_loss_limits():
    result = calculate_position_size(100000, 100, 100, 98, 104, "LONG")

    assert result.risk_amount <= 500
    assert result.planned_risk <= 500
    assert result.planned_capital <= 10000
