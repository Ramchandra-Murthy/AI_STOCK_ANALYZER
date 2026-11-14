"""General-purpose position sizing and pre-trade risk checks."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from algorithmic_trading.trading_profile import TradingProfile

Side = Literal["LONG", "SHORT"]


@dataclass(frozen=True)
class PositionPlan:
    """Position-size calculation with explicit constraints and assumptions."""

    quantity: int
    risk_budget: float
    estimated_loss_at_stop: float
    risk_per_unit: float
    capital_required: float
    side: Side
    allowed: bool
    reason: str


def calculate_position_plan(
    profile: TradingProfile,
    *,
    entry_price: float,
    stop_price: float,
    side: Side = "LONG",
    available_cash: float | None = None,
    current_exposure: float = 0.0,
    daily_loss_so_far: float = 0.0,
) -> PositionPlan:
    """Size a position under risk, capital, exposure, and daily-loss limits.

    Estimated round-trip costs are approximated as a percentage of entry
    notional. Actual brokerage, taxes, slippage, gaps, and market impact can
    differ; callers should replace the estimate with broker-specific costs
    when available.
    """
    numeric = (entry_price, stop_price, current_exposure, daily_loss_so_far)
    if any(isinstance(value, bool) or not math.isfinite(float(value)) for value in numeric):
        raise ValueError("prices, exposure and daily loss must be finite numbers")
    if entry_price <= 0 or stop_price <= 0:
        raise ValueError("entry_price and stop_price must be positive")
    if current_exposure < 0 or daily_loss_so_far < 0:
        raise ValueError("exposure and daily loss cannot be negative")
    if side not in {"LONG", "SHORT"}:
        raise ValueError("side must be LONG or SHORT")
    if side == "LONG" and stop_price >= entry_price:
        raise ValueError("long stop_price must be below entry_price")
    if side == "SHORT" and stop_price <= entry_price:
        raise ValueError("short stop_price must be above entry_price")
    if side == "SHORT" and not profile.allow_short:
        return PositionPlan(0, profile.risk_budget, 0.0, 0.0, 0.0, side, False,
                            "Short selling is disabled in this profile.")

    cash = profile.capital if available_cash is None else float(available_cash)
    if not math.isfinite(cash) or cash < 0:
        raise ValueError("available_cash must be finite and non-negative")
    if daily_loss_so_far >= profile.daily_loss_limit:
        return PositionPlan(0, profile.risk_budget, 0.0, 0.0, 0.0, side, False,
                            "Daily loss limit has been reached.")

    stop_distance = abs(entry_price - stop_price)
    cost_per_unit = entry_price * profile.estimated_round_trip_cost_pct / 100.0
    risk_per_unit = stop_distance + cost_per_unit
    remaining_daily_budget = profile.daily_loss_limit - daily_loss_so_far
    risk_budget = min(profile.risk_budget, remaining_daily_budget)

    exposure_cap = profile.capital * profile.max_exposure_pct / 100.0
    exposure_room = max(0.0, exposure_cap - current_exposure)
    reserve = profile.capital * profile.cash_reserve_pct / 100.0
    cash_room = max(0.0, cash - reserve)
    position_cap = profile.capital * profile.max_position_pct / 100.0
    notional_room = min(exposure_room, cash_room, position_cap)

    quantity_by_risk = math.floor(risk_budget / risk_per_unit)
    quantity_by_capital = math.floor(notional_room / entry_price)
    quantity = max(0, min(quantity_by_risk, quantity_by_capital))
    if quantity == 0:
        return PositionPlan(0, risk_budget, 0.0, risk_per_unit, 0.0, side, False,
                            "No quantity fits all configured risk and capital limits.")

    notional = quantity * entry_price
    estimated_loss = quantity * risk_per_unit
    return PositionPlan(
        quantity=quantity,
        risk_budget=risk_budget,
        estimated_loss_at_stop=estimated_loss,
        risk_per_unit=risk_per_unit,
        capital_required=notional,
        side=side,
        allowed=True,
        reason="Position fits configured risk, cash, position and exposure limits.",
    )
