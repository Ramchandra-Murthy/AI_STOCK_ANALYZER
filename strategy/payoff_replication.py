"""Replicate continuous piecewise-linear expiration payoffs with vanilla options.

This module implements the theoretical construction from Section 2.14.
It is deliberately independent of option valuation, market data, and trading.
All monetary/quantity inputs use Decimal to avoid binary floating-point drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Iterable


class OptionType(StrEnum):
    """Vanilla option type."""

    CALL = "call"
    PUT = "put"


class PositionSide(StrEnum):
    """Long or short option position."""

    LONG = "long"
    SHORT = "short"


@dataclass(frozen=True)
class PayoffPoint:
    """A point on the target expiration-payoff function."""

    underlying: Decimal
    payoff: Decimal

    def __post_init__(self) -> None:
        if self.underlying < 0:
            raise ValueError("underlying values must be non-negative")


@dataclass(frozen=True)
class OptionLeg:
    """One theoretical option position; quantity may be fractional."""

    option_type: OptionType
    side: PositionSide
    strike: Decimal
    quantity: Decimal

    def __post_init__(self) -> None:
        if self.strike < 0:
            raise ValueError("strike must be non-negative")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")

    def expiration_payoff(self, underlying: Decimal) -> Decimal:
        """Return this leg's signed expiration payoff per underlying unit."""
        if underlying < 0:
            raise ValueError("underlying must be non-negative")
        if self.option_type is OptionType.CALL:
            intrinsic = max(underlying - self.strike, Decimal("0"))
        else:
            intrinsic = max(self.strike - underlying, Decimal("0"))
        sign = Decimal("1") if self.side is PositionSide.LONG else Decimal("-1")
        return sign * self.quantity * intrinsic


@dataclass(frozen=True)
class PayoffReplication:
    """Option legs that reproduce a target payoff on the non-negative domain."""

    points: tuple[PayoffPoint, ...]
    terminal_slope: Decimal
    legs: tuple[OptionLeg, ...]

    def expiration_payoff(self, underlying: Decimal) -> Decimal:
        """Evaluate the combined option payoff at expiration."""
        return sum(
            (leg.expiration_payoff(underlying) for leg in self.legs),
            start=Decimal("0"),
        )

    def target_payoff(self, underlying: Decimal) -> Decimal:
        """Evaluate the target piecewise-linear payoff, including extrapolation."""
        if underlying < 0:
            raise ValueError("underlying must be non-negative")
        for left, right in zip(self.points, self.points[1:]):
            if underlying <= right.underlying:
                slope = (right.payoff - left.payoff) / (
                    right.underlying - left.underlying
                )
                return left.payoff + slope * (underlying - left.underlying)
        last = self.points[-1]
        return last.payoff + self.terminal_slope * (underlying - last.underlying)


def _option_leg(
    option_type: OptionType,
    side: PositionSide,
    strike: Decimal,
    quantity: Decimal,
) -> OptionLeg:
    """Create a leg only when its quantity is non-zero."""
    return OptionLeg(option_type, side, strike, abs(quantity))


def _append_signed_call(
    legs: list[OptionLeg], strike: Decimal, slope_change: Decimal
) -> None:
    if slope_change > 0:
        legs.append(_option_leg(OptionType.CALL, PositionSide.LONG, strike, slope_change))
    elif slope_change < 0:
        legs.append(_option_leg(OptionType.CALL, PositionSide.SHORT, strike, slope_change))


def _append_constant_adjustment(legs: list[OptionLeg], amount: Decimal) -> None:
    """Add a four-option package with constant payoff equal to amount."""
    if amount == 0:
        return
    low = Decimal("0")
    high = abs(amount)
    side = PositionSide.LONG if amount > 0 else PositionSide.SHORT
    opposite = PositionSide.SHORT if amount > 0 else PositionSide.LONG

    # Long call(K) + short put(K) + short call(L) + long put(L) = L - K.
    legs.extend(
        (
            _option_leg(OptionType.CALL, side, low, Decimal("1")),
            _option_leg(OptionType.PUT, opposite, low, Decimal("1")),
            _option_leg(OptionType.CALL, opposite, high, Decimal("1")),
            _option_leg(OptionType.PUT, side, high, Decimal("1")),
        )
    )


def replicate_piecewise_linear_payoff(
    points: Iterable[PayoffPoint],
    *,
    terminal_slope: Decimal,
) -> PayoffReplication:
    """Construct the book's call-slope and four-option vertical-offset replication.

    The first point must be at underlying zero. The target is continuous and
    piecewise linear between the supplied points, then continues with
    terminal_slope beyond the final point.
    """
    ordered_points = tuple(points)
    if len(ordered_points) < 2:
        raise ValueError("at least two payoff points are required")
    if ordered_points[0].underlying != 0:
        raise ValueError("the first payoff point must have underlying equal to zero")
    if any(
        right.underlying <= left.underlying
        for left, right in zip(ordered_points, ordered_points[1:])
    ):
        raise ValueError("underlying values must be strictly increasing")

    segment_slopes = tuple(
        (right.payoff - left.payoff) / (right.underlying - left.underlying)
        for left, right in zip(ordered_points, ordered_points[1:])
    )

    legs: list[OptionLeg] = []
    _append_signed_call(legs, ordered_points[0].underlying, segment_slopes[0])

    for index in range(1, len(ordered_points)):
        previous_slope = segment_slopes[index - 1]
        next_slope = (
            segment_slopes[index]
            if index < len(segment_slopes)
            else terminal_slope
        )
        _append_signed_call(
            legs,
            ordered_points[index].underlying,
            next_slope - previous_slope,
        )

    # Calls with non-negative strikes pay zero at S_T = 0. Correct the
    # remaining vertical offset with the book's four-option constant package.
    vertical_offset = ordered_points[0].payoff
    _append_constant_adjustment(legs, vertical_offset)

    return PayoffReplication(
        points=ordered_points,
        terminal_slope=terminal_slope,
        legs=tuple(legs),
    )
