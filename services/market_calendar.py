"""Shared NSE/BSE equity calendar for regular-session safety checks.

Holiday dates are sourced from exchange-published calendars and must be updated
when the exchange publishes a new annual calendar or an amendment. Unknown years
are deliberately treated as unavailable during would-be session hours; callers
must not assume that an unconfigured year is a trading day.
"""

from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
REGULAR_SESSION_OPEN = time(9, 15)
REGULAR_SESSION_CLOSE = time(15, 30)

# NSE's 2026 equity holiday calendar, including the January 15 Maharashtra
# municipal-election holiday and August 26 Id-E-Milad. Review exchange notices
# for amendments before relying on a new calendar year.
EQUITY_HOLIDAYS_BY_YEAR: dict[int, frozenset[date]] = {
    2026: frozenset(
        {
            date(2026, 1, 15),
            date(2026, 1, 26),
            date(2026, 3, 3),
            date(2026, 3, 21),  # Saturday holiday; retained for calendar completeness.
            date(2026, 3, 26),
            date(2026, 3, 31),
            date(2026, 4, 3),
            date(2026, 4, 14),
            date(2026, 5, 1),
            date(2026, 5, 28),
            date(2026, 6, 26),
            date(2026, 8, 26),
            date(2026, 9, 14),
            date(2026, 10, 2),
            date(2026, 10, 20),
            date(2026, 11, 8),  # Normal session closed; Muhurat schedule needs its own notice.
            date(2026, 11, 10),
            date(2026, 11, 24),
            date(2026, 12, 25),
        }
    ),
}


def is_equity_calendar_year_supported(year: int) -> bool:
    """Return whether an exchange-verified holiday calendar is configured for year."""
    return year in EQUITY_HOLIDAYS_BY_YEAR


def is_equity_market_holiday(day: date) -> bool:
    """Return whether day is a listed full-day equity holiday in a supported year."""
    return day in EQUITY_HOLIDAYS_BY_YEAR.get(day.year, frozenset())


def equity_market_session_status(
    now: datetime,
    open_time: time = REGULAR_SESSION_OPEN,
    close_time: time = REGULAR_SESSION_CLOSE,
) -> str:
    """Classify regular-session status as OPEN, CLOSED, HOLIDAY, or CALENDAR_UNAVAILABLE.

    This intentionally does not enable special sessions such as Muhurat Trading.
    Those require a separate, exchange-published session window.
    """
    current = now.replace(tzinfo=IST) if now.tzinfo is None else now.astimezone(IST)
    if current.weekday() >= 5:
        return "CLOSED"
    current_time = current.time().replace(tzinfo=None, microsecond=0)
    if not open_time <= current_time < close_time:
        return "CLOSED"
    if not is_equity_calendar_year_supported(current.year):
        return "CALENDAR_UNAVAILABLE"
    if is_equity_market_holiday(current.date()):
        return "HOLIDAY"
    return "OPEN"


def is_regular_equity_session_open(now: datetime) -> bool:
    """Return true only when the configured calendar confirms a regular session."""
    return equity_market_session_status(now) == "OPEN"
