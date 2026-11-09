"""Volume-constrained execution simulation with a transparent square-root impact model.

This is a bar-level research approximation, not an order-book or broker fill model.
Volatility is supplied as a decimal return (for example, 0.02 for 2%).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExecutionFillDiagnostics:
    """Order-level completion and implementation-shortfall summary."""

    side: str
    requested_quantity: float
    filled_quantity: float
    remaining_quantity: float
    fill_ratio: float
    arrival_price: float
    volume_weighted_price: float | None
    slippage_bps: float | None
    implementation_shortfall: float | None
    total_executed_notional: float
    total_market_volume: float
    average_participation_rate: float
    maximum_participation_rate: float
    bars_observed: int
    bars_to_complete: int | None
    completed: bool


def estimate_market_impact_bps(
    *,
    filled_quantity: float,
    bar_volume: float,
    volatility: float,
    impact_coefficient: float = 0.5,
    half_spread_bps: float = 0.0,
) -> float:
    """Estimate one-way spread plus square-root temporary impact in basis points."""
    values = (filled_quantity, bar_volume, volatility, impact_coefficient, half_spread_bps)
    if not all(np.isfinite(value) for value in values):
        raise ValueError("impact inputs must be finite")
    if filled_quantity < 0 or bar_volume <= 0 or volatility < 0:
        raise ValueError("quantity and volatility must be non-negative; volume must be positive")
    if impact_coefficient < 0 or half_spread_bps < 0:
        raise ValueError("impact coefficient and half_spread_bps must be non-negative")
    if filled_quantity > bar_volume:
        raise ValueError("filled_quantity cannot exceed bar_volume")

    participation = filled_quantity / bar_volume
    impact = impact_coefficient * volatility * np.sqrt(participation) * 10_000.0
    return float(half_spread_bps + impact)


def simulate_execution(
    *,
    order_quantity: float,
    side: str,
    prices: pd.Series,
    volumes: pd.Series,
    volatility: pd.Series,
    max_participation: float = 0.10,
    impact_coefficient: float = 0.5,
    half_spread_bps: float = 0.0,
) -> pd.DataFrame:
    """Fill an order sequentially subject to bar-volume participation limits.

    A buy pays above the reference bar price and a sell receives below it.
    Unfilled quantity remains outstanding at the end of the supplied bars.
    No future bar is used to determine an earlier fill.
    """
    if not np.isfinite(order_quantity) or order_quantity <= 0:
        raise ValueError("order_quantity must be finite and greater than zero")
    if side not in {"buy", "sell"}:
        raise ValueError("side must be 'buy' or 'sell'")
    if not np.isfinite(max_participation) or not 0 < max_participation <= 1:
        raise ValueError("max_participation must be in (0, 1]")
    if not prices.index.is_unique or not volumes.index.is_unique or not volatility.index.is_unique:
        raise ValueError("input indexes must not contain duplicate timestamps")
    if not prices.index.equals(volumes.index) or not prices.index.equals(volatility.index):
        raise ValueError("prices, volumes, and volatility must have identical indexes")
    if prices.empty:
        raise ValueError("at least one bar is required")

    frame = pd.DataFrame(
        {
            "reference_price": pd.to_numeric(prices, errors="coerce"),
            "bar_volume": pd.to_numeric(volumes, errors="coerce"),
            "volatility": pd.to_numeric(volatility, errors="coerce"),
        },
        index=prices.index,
    )
    if not np.isfinite(frame.to_numpy(dtype=float)).all():
        raise ValueError("prices, volumes, and volatility must be finite numeric values")
    if (frame["reference_price"] <= 0).any():
        raise ValueError("prices must be greater than zero")
    if (frame["bar_volume"] < 0).any() or (frame["volatility"] < 0).any():
        raise ValueError("volumes and volatility must be non-negative")

    remaining = float(order_quantity)
    rows: list[dict[str, float]] = []
    direction = 1.0 if side == "buy" else -1.0

    for _, bar in frame.iterrows():
        capacity = float(bar["bar_volume"]) * max_participation
        filled = min(remaining, capacity)
        if filled > 0 and bar["bar_volume"] > 0:
            impact_bps = estimate_market_impact_bps(
                filled_quantity=filled,
                bar_volume=float(bar["bar_volume"]),
                volatility=float(bar["volatility"]),
                impact_coefficient=impact_coefficient,
                half_spread_bps=half_spread_bps,
            )
        else:
            impact_bps = 0.0
        reference_price = float(bar["reference_price"])
        execution_price = reference_price * (1.0 + direction * impact_bps / 10_000.0)
        remaining -= filled
        rows.append(
            {
                "reference_price": reference_price,
                "bar_volume": float(bar["bar_volume"]),
                "filled_quantity": filled,
                "remaining_quantity": remaining,
                "participation_rate": (
                    filled / float(bar["bar_volume"]) if bar["bar_volume"] > 0 else 0.0
                ),
                "impact_bps": impact_bps,
                "execution_price": execution_price,
                "executed_notional": filled * execution_price,
            }
        )

    result = pd.DataFrame(rows, index=frame.index)
    result.index.name = prices.index.name
    return result


def summarize_execution_fills(
    fills: pd.DataFrame,
    *,
    order_quantity: float,
    side: str,
    arrival_price: float,
) -> ExecutionFillDiagnostics:
    """Summarize simulated fills against an explicit arrival-price benchmark.

    The function accepts the output of :func:`simulate_execution`. Slippage is
    positive when execution is worse than arrival price for either side.
    Brokerage, statutory charges and taxes are deliberately excluded.
    """
    if side not in {"buy", "sell"}:
        raise ValueError("side must be 'buy' or 'sell'")
    if not np.isfinite(order_quantity) or order_quantity <= 0:
        raise ValueError("order_quantity must be finite and greater than zero")
    if not np.isfinite(arrival_price) or arrival_price <= 0:
        raise ValueError("arrival_price must be finite and greater than zero")
    required = {
        "bar_volume",
        "filled_quantity",
        "remaining_quantity",
        "execution_price",
        "participation_rate",
    }
    missing = required.difference(fills.columns)
    if missing:
        raise ValueError(f"fills missing required columns: {sorted(missing)}")
    if fills.empty:
        raise ValueError("fills must contain at least one observed bar")
    values = fills[list(required)].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ValueError("fill diagnostics inputs must be finite numeric values")
    if (values[["bar_volume", "filled_quantity", "remaining_quantity", "participation_rate"]] < 0).any().any():
        raise ValueError("fill quantities, volume, and participation must be non-negative")
    if (values["execution_price"] <= 0).any():
        raise ValueError("execution prices must be greater than zero")

    filled_quantity = float(values["filled_quantity"].sum())
    tolerance = max(1e-9, float(order_quantity) * 1e-12)
    if filled_quantity > order_quantity + tolerance:
        raise ValueError("total filled quantity cannot exceed order quantity")
    remaining_quantity = max(float(order_quantity) - filled_quantity, 0.0)
    reported_remaining = float(values["remaining_quantity"].iloc[-1])
    if not np.isclose(reported_remaining, remaining_quantity, rtol=1e-9, atol=tolerance):
        raise ValueError("final remaining quantity does not reconcile to cumulative fills")

    executed_notional = float(
        (values["filled_quantity"] * values["execution_price"]).sum()
    )
    vwap = executed_notional / filled_quantity if filled_quantity > 0 else None
    direction = 1.0 if side == "buy" else -1.0
    slippage_bps = (
        direction * (vwap / arrival_price - 1.0) * 10_000.0 if vwap is not None else None
    )
    shortfall = (
        direction * (vwap - arrival_price) * filled_quantity if vwap is not None else None
    )
    total_volume = float(values["bar_volume"].sum())
    average_participation = filled_quantity / total_volume if total_volume > 0 else 0.0
    completion_positions = np.flatnonzero(values["remaining_quantity"].to_numpy() <= tolerance)
    bars_to_complete = int(completion_positions[0] + 1) if len(completion_positions) else None

    return ExecutionFillDiagnostics(
        side=side,
        requested_quantity=float(order_quantity),
        filled_quantity=filled_quantity,
        remaining_quantity=remaining_quantity,
        fill_ratio=filled_quantity / float(order_quantity),
        arrival_price=float(arrival_price),
        volume_weighted_price=vwap,
        slippage_bps=slippage_bps,
        implementation_shortfall=shortfall,
        total_executed_notional=executed_notional,
        total_market_volume=total_volume,
        average_participation_rate=average_participation,
        maximum_participation_rate=float(values["participation_rate"].max()),
        bars_observed=len(values),
        bars_to_complete=bars_to_complete,
        completed=remaining_quantity <= tolerance,
    )
