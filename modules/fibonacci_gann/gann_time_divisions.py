"""Explicit bar-index interval divisions for Gann-style research.

Positions are arithmetic reference points only; this helper does not infer
market cycles or claim that projected dates or bars are predictive.
"""

from __future__ import annotations

from math import isfinite

DEFAULT_GANN_TIME_DIVISIONS = 8


def gann_time_divisions(
    start_bar: int | float,
    end_bar: int | float,
    *,
    divisions: int = DEFAULT_GANN_TIME_DIVISIONS,
) -> dict[float, float]:
    """Return equally spaced bar positions keyed by fractional interval.

    Endpoints are caller-supplied bar indices or positions. The order is
    preserved, so descending intervals are supported. Intermediate positions
    can be fractional when the interval is not evenly divisible into whole bars.
    """
    for name, value in (("start_bar", start_bar), ("end_bar", end_bar)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            raise ValueError(f"{name} must be a finite number")
    if start_bar == end_bar:
        raise ValueError("start_bar and end_bar must differ")
    if isinstance(divisions, bool) or not isinstance(divisions, int) or divisions < 1:
        raise ValueError("divisions must be a positive integer")

    start = float(start_bar)
    span = float(end_bar) - start
    return {index / divisions: start + span * index / divisions for index in range(divisions + 1)}
