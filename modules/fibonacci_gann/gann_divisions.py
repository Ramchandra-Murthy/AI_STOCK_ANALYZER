"""Explicit price-range divisions for Gann-style research.

This helper divides a caller-supplied range into equal fractional intervals.
It does not infer trading ranges or claim that any level is predictive.
"""

from __future__ import annotations

from math import isfinite

DEFAULT_GANN_DIVISIONS = 8


def gann_price_divisions(
    range_start: float,
    range_end: float,
    *,
    divisions: int = DEFAULT_GANN_DIVISIONS,
) -> dict[float, float]:
    """Return equally spaced price levels keyed by fractional position.

    The returned keys run from 0.0 through 1.0 inclusive. The endpoints
    preserve the supplied order, so descending ranges are supported too.
    """
    for name, value in (("range_start", range_start), ("range_end", range_end)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            raise ValueError(f"{name} must be a finite number")
    if range_start == range_end:
        raise ValueError("range_start and range_end must differ")
    if isinstance(divisions, bool) or not isinstance(divisions, int) or divisions < 1:
        raise ValueError("divisions must be a positive integer")

    start = float(range_start)
    span = float(range_end) - start
    return {index / divisions: start + span * index / divisions for index in range(divisions + 1)}
