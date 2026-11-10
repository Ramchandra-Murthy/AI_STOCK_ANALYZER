"""Helpers for controlled intraday dashboard auto-refresh."""

from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

INDIA_TIMEZONE = ZoneInfo("Asia/Kolkata")
MARKET_OPEN = time(9, 15)
FIRST_SCAN_TIME = time(9, 25)
MARKET_CLOSE = time(15, 30)
DEFAULT_REFRESH_SECONDS = 300
ALLOWED_REFRESH_SECONDS = (60, 120, 300, 600)


def _as_india_time(value: datetime | None) -> datetime:
    """Normalize a timestamp to IST; treat naive values as local Indian time."""
    if value is None:
        return datetime.now(INDIA_TIMEZONE)
    if value.tzinfo is None:
        return value.replace(tzinfo=INDIA_TIMEZONE)
    return value.astimezone(INDIA_TIMEZONE)


def market_is_open(now: datetime | None = None) -> bool:
    """Return whether the NSE cash session is currently open on a weekday."""
    current = _as_india_time(now)
    return current.weekday() < 5 and MARKET_OPEN <= current.time() < MARKET_CLOSE


def seconds_until_first_scan(now: datetime | None = None) -> int:
    """Return seconds until the first automatic scan is allowed at 09:25 IST."""
    current = _as_india_time(now)
    if current.time() >= FIRST_SCAN_TIME:
        return 0
    target = current.replace(
        hour=FIRST_SCAN_TIME.hour,
        minute=FIRST_SCAN_TIME.minute,
        second=0,
        microsecond=0,
    )
    return max(0, int((target - current).total_seconds()))


def next_refresh_seconds(
    last_scan_at: datetime | None,
    interval_seconds: int = DEFAULT_REFRESH_SECONDS,
    now: datetime | None = None,
) -> int:
    """Return whole seconds until the next scheduled refresh."""
    current = _as_india_time(now)
    if last_scan_at is None:
        return 0

    last = _as_india_time(last_scan_at)
    elapsed = max(0, int((current - last).total_seconds()))
    return max(0, interval_seconds - elapsed)


def refresh_label(seconds: int) -> str:
    """Format a refresh countdown for compact dashboard display."""
    if seconds <= 0:
        return "refresh due"
    minutes, remaining = divmod(seconds, 60)
    return f"{minutes}m {remaining:02d}s" if minutes else f"{remaining}s"
