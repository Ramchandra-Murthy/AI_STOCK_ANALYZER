"""Depth-aware market-order execution estimates from validated Level-2 snapshots.

This is a static-book sweep approximation. It does not model queue priority,
book replenishment, cancellations during execution, latency, or hidden liquidity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from ai_trading.order_book import OrderBookSnapshot


@dataclass(frozen=True)
class OrderBookExecutionEstimate:
    """Estimated fills and implementation-shortfall diagnostics for one sweep."""

    symbol: str
    side: str
    requested_quantity: float
    filled_quantity: float
    remaining_quantity: float
    fill_ratio: float
    reference_mid_price: float
    best_executable_price: float
    volume_weighted_price: float | None
    executed_notional: float
    implementation_shortfall_bps: float | None
    book_walk_bps: float | None
    levels_touched: int
    fills: pd.DataFrame


def estimate_order_book_execution(
    snapshot: OrderBookSnapshot,
    *,
    side: str,
    quantity: float,
    synchronized: bool,
    max_levels: int | None = None,
) -> OrderBookExecutionEstimate:
    """Sweep displayed ask depth for buys or bid depth for sells.

    The caller must pass synchronized=True only when upstream feed/replay state
    confirms continuity. Unsynchronized books are rejected.
    """
    if not isinstance(snapshot, OrderBookSnapshot):
        raise TypeError("snapshot must be an OrderBookSnapshot")
    if not isinstance(synchronized, bool) or not synchronized:
        raise ValueError("order book must be explicitly confirmed synchronized")
    if side not in {"buy", "sell"}:
        raise ValueError("side must be 'buy' or 'sell'")
    if isinstance(quantity, bool):
        raise ValueError("quantity must be finite and greater than zero")
    try:
        requested = float(quantity)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("quantity must be numeric") from exc
    if not math.isfinite(requested) or requested <= 0:
        raise ValueError("quantity must be finite and greater than zero")
    if max_levels is not None and (
        isinstance(max_levels, bool) or not isinstance(max_levels, int) or max_levels < 1
    ):
        raise ValueError("max_levels must be a positive integer or None")

    levels = snapshot.asks if side == "buy" else snapshot.bids
    if max_levels is not None:
        levels = levels[:max_levels]
    best_price = levels[0].price
    mid_price = snapshot.metrics(levels=1).mid_price
    remaining = requested
    rows: list[dict[str, float]] = []

    for level_number, level in enumerate(levels, start=1):
        if remaining <= 0:
            break
        filled = min(remaining, level.quantity)
        if filled <= 0:
            continue
        rows.append(
            {
                "level": float(level_number),
                "price": level.price,
                "available_quantity": level.quantity,
                "filled_quantity": filled,
                "executed_notional": filled * level.price,
            }
        )
        remaining -= filled

    fills = pd.DataFrame(
        rows,
        columns=["level", "price", "available_quantity", "filled_quantity", "executed_notional"],
    )
    filled_quantity = requested - remaining
    executed_notional = float(fills["executed_notional"].sum()) if not fills.empty else 0.0
    vwap = executed_notional / filled_quantity if filled_quantity > 0 else None
    direction = 1.0 if side == "buy" else -1.0
    shortfall = direction * (vwap / mid_price - 1.0) * 10_000.0 if vwap is not None else None
    book_walk = direction * (vwap / best_price - 1.0) * 10_000.0 if vwap is not None else None

    return OrderBookExecutionEstimate(
        symbol=snapshot.symbol,
        side=side,
        requested_quantity=requested,
        filled_quantity=filled_quantity,
        remaining_quantity=remaining,
        fill_ratio=filled_quantity / requested,
        reference_mid_price=mid_price,
        best_executable_price=best_price,
        volume_weighted_price=vwap,
        executed_notional=executed_notional,
        implementation_shortfall_bps=shortfall,
        book_walk_bps=book_walk,
        levels_touched=len(rows),
        fills=fills,
    )
