"""Validated level-2 order-book snapshots and aggregate-level updates.

This module accepts normalized price-level data from an upstream market-data
adapter. It does not connect to an exchange, infer hidden liquidity, or model
individual order queue priority.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Literal

BookSide = Literal["bid", "ask"]


def _positive_finite(value: float, field: str, *, allow_zero: bool = False) -> float:
    """Convert a numeric value to float and enforce finite positive quantities."""
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite {'non-negative' if allow_zero else 'positive'} number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or (number < 0 if allow_zero else number <= 0):
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{field} must be finite and {qualifier}")
    return number


def _aware_timestamp(value: datetime | str) -> datetime:
    """Parse an ISO timestamp and reject naive timestamps with ambiguous timezone."""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("timestamp must be an ISO-8601 datetime") from exc
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value


@dataclass(frozen=True, slots=True)
class OrderBookLevel:
    """One aggregated price level; quantity is the displayed total at that price."""

    price: float
    quantity: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "price", _positive_finite(self.price, "price"))
        object.__setattr__(self, "quantity", _positive_finite(self.quantity, "quantity"))


@dataclass(frozen=True, slots=True)
class LevelUpdate:
    """Absolute displayed quantity for one side/price; zero removes that level.

    This is deliberately an absolute SET/DELETE contract. Provider-specific
    event quantities must be decoded by the adapter before constructing it.
    """

    timestamp: datetime | str
    side: BookSide
    price: float
    quantity: float
    sequence: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", _aware_timestamp(self.timestamp))
        if self.side not in ("bid", "ask"):
            raise ValueError("side must be 'bid' or 'ask'")
        object.__setattr__(self, "price", _positive_finite(self.price, "price"))
        object.__setattr__(
            self, "quantity", _positive_finite(self.quantity, "quantity", allow_zero=True)
        )
        if self.sequence is not None and (
            isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence < 0
        ):
            raise ValueError("sequence must be a non-negative integer or None")


@dataclass(frozen=True, slots=True)
class OrderBookMetrics:
    """Top-of-book and cumulative-depth metrics for one snapshot."""

    best_bid: float
    best_ask: float
    mid_price: float
    spread: float
    spread_bps: float
    bid_depth: float
    ask_depth: float
    depth_imbalance: float
    microprice: float
    bid_top_level_concentration: float
    ask_top_level_concentration: float
    levels_used: int


@dataclass(frozen=True, slots=True)
class OrderBookSnapshot:
    """Immutable aggregated L2 book snapshot with bids/asks sorted best-first."""

    symbol: str
    timestamp: datetime | str
    bids: tuple[OrderBookLevel, ...]
    asks: tuple[OrderBookLevel, ...]
    sequence: int | None = None

    def __post_init__(self) -> None:
        symbol = str(self.symbol).strip().upper()
        if not symbol:
            raise ValueError("symbol must be non-empty")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "timestamp", _aware_timestamp(self.timestamp))
        bids = tuple(self.bids)
        asks = tuple(self.asks)
        if not bids or not asks:
            raise ValueError("both bid and ask sides must contain at least one level")
        if not all(isinstance(level, OrderBookLevel) for level in (*bids, *asks)):
            raise ValueError("bids and asks must contain OrderBookLevel values")
        if len({level.price for level in bids}) != len(bids):
            raise ValueError("duplicate bid prices are not allowed")
        if len({level.price for level in asks}) != len(asks):
            raise ValueError("duplicate ask prices are not allowed")
        bids = tuple(sorted(bids, key=lambda level: level.price, reverse=True))
        asks = tuple(sorted(asks, key=lambda level: level.price))
        if bids[0].price >= asks[0].price:
            raise ValueError("book must not be locked or crossed (best bid must be below best ask)")
        object.__setattr__(self, "bids", bids)
        object.__setattr__(self, "asks", asks)
        if self.sequence is not None and (
            isinstance(self.sequence, bool)
            or not isinstance(self.sequence, int)
            or self.sequence < 0
        ):
            raise ValueError("sequence must be a non-negative integer or None")

    @classmethod
    def from_levels(
        cls,
        symbol: str,
        timestamp: datetime | str,
        bids: Iterable[tuple[float, float]],
        asks: Iterable[tuple[float, float]],
        *,
        sequence: int | None = None,
    ) -> OrderBookSnapshot:
        """Build a normalized snapshot from (price, absolute_quantity) pairs."""
        return cls(
            symbol=symbol,
            timestamp=timestamp,
            bids=tuple(OrderBookLevel(price, quantity) for price, quantity in bids),
            asks=tuple(OrderBookLevel(price, quantity) for price, quantity in asks),
            sequence=sequence,
        )

    def apply_update(self, update: LevelUpdate) -> OrderBookSnapshot:
        """Return a new snapshot after an absolute level SET or DELETE update."""
        if not isinstance(update, LevelUpdate):
            raise ValueError("update must be a LevelUpdate")
        if update.timestamp < self.timestamp:
            raise ValueError("update timestamp cannot precede the current snapshot")
        if (
            self.sequence is not None
            and update.sequence is not None
            and update.sequence <= self.sequence
        ):
            raise ValueError("update sequence must be greater than the current sequence")

        side_levels = list(self.bids if update.side == "bid" else self.asks)
        existing = next((i for i, level in enumerate(side_levels) if level.price == update.price), None)
        if update.quantity == 0.0:
            if existing is not None:
                side_levels.pop(existing)
        elif existing is None:
            side_levels.append(OrderBookLevel(update.price, update.quantity))
        else:
            side_levels[existing] = OrderBookLevel(update.price, update.quantity)

        bids = side_levels if update.side == "bid" else self.bids
        asks = side_levels if update.side == "ask" else self.asks
        return OrderBookSnapshot(
            symbol=self.symbol,
            timestamp=update.timestamp,
            bids=tuple(bids),
            asks=tuple(asks),
            sequence=update.sequence if update.sequence is not None else self.sequence,
        )

    def metrics(self, *, levels: int = 5) -> OrderBookMetrics:
        """Calculate transparent top-N liquidity metrics from displayed depth."""
        if isinstance(levels, bool) or not isinstance(levels, int) or levels < 1:
            raise ValueError("levels must be a positive integer")
        bids = self.bids[:levels]
        asks = self.asks[:levels]
        bid_depth = sum(level.quantity for level in bids)
        ask_depth = sum(level.quantity for level in asks)
        total_depth = bid_depth + ask_depth
        best_bid = self.bids[0]
        best_ask = self.asks[0]
        mid = (best_bid.price + best_ask.price) / 2.0
        spread = best_ask.price - best_bid.price
        imbalance = (bid_depth - ask_depth) / total_depth if total_depth else 0.0
        top_total = best_bid.quantity + best_ask.quantity
        microprice = (
            (best_ask.price * best_bid.quantity + best_bid.price * best_ask.quantity)
            / top_total
        )
        return OrderBookMetrics(
            best_bid=best_bid.price,
            best_ask=best_ask.price,
            mid_price=mid,
            spread=spread,
            spread_bps=spread / mid * 10_000.0,
            bid_depth=bid_depth,
            ask_depth=ask_depth,
            depth_imbalance=imbalance,
            microprice=microprice,
            bid_top_level_concentration=best_bid.quantity / bid_depth,
            ask_top_level_concentration=best_ask.quantity / ask_depth,
            levels_used=min(levels, len(self.bids), len(self.asks)),
        )
