from datetime import date, datetime
from zoneinfo import ZoneInfo

from modules.intraday import _is_equity_market_holiday, _market_session_is_open


IST = ZoneInfo("Asia/Kolkata")


def test_october_2_2026_is_an_equity_market_holiday() -> None:
    assert _is_equity_market_holiday(date(2026, 10, 2))


def test_market_is_closed_on_october_2_2026_during_regular_hours() -> None:
    assert not _market_session_is_open(datetime(2026, 10, 2, 14, 30, tzinfo=IST))


def test_regular_weekday_session_remains_open() -> None:
    assert _market_session_is_open(datetime(2026, 10, 1, 14, 30, tzinfo=IST))


def test_weekend_remains_closed() -> None:
    assert not _market_session_is_open(datetime(2026, 10, 3, 14, 30, tzinfo=IST))
