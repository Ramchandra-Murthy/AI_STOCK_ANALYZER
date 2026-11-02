"""Classify freshness of intraday candle timestamps."""

from datetime import datetime, timedelta
from typing import Any

import pandas as pd


def intraday_context_freshness(
    latest_timestamp: Any,
    *,
    now: datetime,
    max_age: timedelta = timedelta(minutes=5),
) -> str:
    """Return FRESH, STALE, FUTURE_TIMESTAMP, or TIMESTAMP_UNAVAILABLE.

    Naive timestamps are interpreted in the timezone of ``now`` when it is
    timezone-aware. This function does not infer market-session status.
    """
    if latest_timestamp is None:
        return "TIMESTAMP_UNAVAILABLE"
    try:
        observed = pd.Timestamp(latest_timestamp).to_pydatetime()
    except (TypeError, ValueError, OverflowError):
        return "TIMESTAMP_UNAVAILABLE"
    if pd.isna(observed):
        return "TIMESTAMP_UNAVAILABLE"

    if observed.tzinfo is None and now.tzinfo is not None:
        observed = observed.replace(tzinfo=now.tzinfo)
    elif observed.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=observed.tzinfo)
    elif observed.tzinfo is not None and now.tzinfo is not None:
        observed = observed.astimezone(now.tzinfo)

    age = now - observed
    if age < timedelta(0):
        return "FUTURE_TIMESTAMP"
    return "FRESH" if age <= max_age else "STALE"
