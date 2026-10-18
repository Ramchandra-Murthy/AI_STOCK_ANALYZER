from datetime import date, datetime
from zoneinfo import ZoneInfo

from services.market_calendar import (
    equity_market_session_status,
    is_equity_calendar_year_supported,
    is_equity_market_holiday,
    is_regular_equity_session_open,
)

IST = ZoneInfo("Asia/Kolkata")


def test_exchange_calendar_includes_2026_holidays() -> None:
    assert is_equity_calendar_year_supported(2026)
    assert is_equity_market_holiday(date(2026, 1, 15))
    assert is_equity_market_holiday(date(2026, 8, 26))
    assert is_equity_market_holiday(date(2026, 10, 20))


def test_regular_session_is_closed_on_exchange_holiday() -> None:
    assert equity_market_session_status(datetime(2026, 10, 20, 10, 0, tzinfo=IST)) == "HOLIDAY"
    assert not is_regular_equity_session_open(datetime(2026, 10, 20, 10, 0, tzinfo=IST))


def test_regular_session_is_open_on_supported_non_holiday_weekday() -> None:
    assert equity_market_session_status(datetime(2026, 10, 19, 10, 0, tzinfo=IST)) == "OPEN"
    assert is_regular_equity_session_open(datetime(2026, 10, 19, 10, 0, tzinfo=IST))


def test_weekends_and_outside_hours_are_closed() -> None:
    assert equity_market_session_status(datetime(2026, 10, 18, 10, 0, tzinfo=IST)) == "CLOSED"
    assert equity_market_session_status(datetime(2026, 10, 19, 8, 59, tzinfo=IST)) == "CLOSED"


def test_unconfigured_calendar_year_fails_closed_during_session_hours() -> None:
    now = datetime(2027, 1, 4, 10, 0, tzinfo=IST)
    assert not is_equity_calendar_year_supported(2027)
    assert equity_market_session_status(now) == "CALENDAR_UNAVAILABLE"
    assert not is_regular_equity_session_open(now)
