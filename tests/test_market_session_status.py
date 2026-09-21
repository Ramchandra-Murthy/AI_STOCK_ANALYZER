"""Tests for market-session status helpers."""

# ruff: isort: skip_file

from datetime import datetime
from zoneinfo import ZoneInfo

from services.market_service import market_session_status  # noqa: I001


IST = ZoneInfo("Asia/Kolkata")


def test_market_status_marks_previous_session_as_closed():
    now = datetime(2026, 9, 20, 12, 0, tzinfo=IST)
    status = market_session_status("2026-09-18T15:29:00+05:30", "intraday_1m", now)

    assert status["status"] == "MARKET CLOSED · WEEKEND"
    assert status["is_current_session"] is False


def test_market_status_marks_today_intraday_data():
    now = datetime(2026, 9, 18, 12, 0, tzinfo=IST)
    status = market_session_status("2026-09-18T11:59:00+05:30", "intraday_1m", now)

    assert status["status"] == "INTRADAY DATA · TODAY"
    assert status["is_current_session"] is True
    assert status["is_market_open"] is True


def test_market_status_marks_after_close_today_data():
    now = datetime(2026, 9, 18, 16, 0, tzinfo=IST)
    status = market_session_status("2026-09-18T15:29:00+05:30", "intraday_1m", now)

    assert status["status"] == "MARKET CLOSED · TODAY'S DATA"
    assert status["is_current_session"] is True
    assert status["is_market_open"] is False
