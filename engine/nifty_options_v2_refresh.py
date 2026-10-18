"""Refresh scheduling helpers for NIFTY Options V2 paper trading."""

# ruff: noqa: I001

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

from services.market_calendar import equity_market_session_status

IST = ZoneInfo("Asia/Kolkata")


@dataclass(frozen=True)
class MarketRefreshPolicy:
    """NSE market-hours refresh policy."""

    interval_seconds: int = 60
    open_time: time = time(9, 15)
    close_time: time = time(15, 30)

    def __post_init__(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")


def is_market_hours(
    current: datetime,
    policy: MarketRefreshPolicy | None = None,
) -> bool:
    """Return whether a timestamp falls inside the configured weekday session."""
    selected = policy or MarketRefreshPolicy()
    localized = current.astimezone(IST)
    return (
        equity_market_session_status(localized, selected.open_time, selected.close_time) == "OPEN"
    )


def refresh_seconds(policy: MarketRefreshPolicy | None = None) -> int:
    """Return the configured refresh interval for the Streamlit fragment."""
    return (policy or MarketRefreshPolicy()).interval_seconds
