"""Tests for reusable trading profiles and position risk calculations."""

import pytest

from algorithmic_trading.risk_engine import calculate_position_plan
from algorithmic_trading.trading_profile import TradingProfile


def test_profile_is_not_tied_to_a_fixed_account_size() -> None:
    profile = TradingProfile(capital=2_500_000, risk_mode="percent", risk_value=0.75)
    assert profile.risk_budget == pytest.approx(18_750)
    assert profile.daily_loss_limit == pytest.approx(75_000)


def test_position_plan_respects_risk_and_capital_limits() -> None:
    profile = TradingProfile(
        capital=100_000,
        risk_value=1,
        max_position_pct=50,
        max_exposure_pct=80,
        cash_reserve_pct=0,
        estimated_round_trip_cost_pct=0,
    )
    plan = calculate_position_plan(profile, entry_price=250, stop_price=245)
    assert plan.allowed
    assert plan.quantity == 200
    assert plan.estimated_loss_at_stop == pytest.approx(1_000)
    assert plan.capital_required == pytest.approx(50_000)


def test_cost_estimate_reduces_position_size() -> None:
    profile = TradingProfile(
        capital=100_000,
        risk_value=1,
        max_position_pct=100,
        max_exposure_pct=100,
        cash_reserve_pct=0,
        estimated_round_trip_cost_pct=1,
    )
    plan = calculate_position_plan(profile, entry_price=100, stop_price=95)
    assert plan.allowed
    assert plan.quantity == 166
    assert plan.estimated_loss_at_stop <= plan.risk_budget


def test_short_requires_explicit_profile_permission() -> None:
    profile = TradingProfile()
    plan = calculate_position_plan(profile, entry_price=100, stop_price=105, side="SHORT")
    assert not plan.allowed
    assert plan.quantity == 0


def test_short_position_can_be_sized_when_enabled() -> None:
    profile = TradingProfile(
        allow_short=True,
        capital=100_000,
        risk_value=1,
        max_position_pct=100,
        max_exposure_pct=100,
        cash_reserve_pct=0,
        estimated_round_trip_cost_pct=0,
    )
    plan = calculate_position_plan(profile, entry_price=100, stop_price=105, side="SHORT")
    assert plan.allowed
    assert plan.quantity == 200


def test_daily_loss_limit_blocks_new_positions() -> None:
    profile = TradingProfile(capital=100_000, max_daily_loss_pct=2)
    plan = calculate_position_plan(profile, entry_price=100, stop_price=95, daily_loss_so_far=2_000)
    assert not plan.allowed
    assert "Daily loss limit" in plan.reason


@pytest.mark.parametrize(
    "kwargs",
    [
        {"capital": 0},
        {"risk_value": 0},
        {"max_positions": 0},
        {"max_position_pct": 90, "max_exposure_pct": 80},
    ],
)
def test_invalid_profiles_are_rejected(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        TradingProfile(**kwargs)
