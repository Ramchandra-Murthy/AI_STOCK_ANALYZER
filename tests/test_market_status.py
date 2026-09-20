from datetime import datetime

from services.market_status import describe_market_status


def test_closed_status_for_previous_session():
    status = describe_market_status(
        "2026-09-18T15:29:00+05:30",
        datetime(2026, 9, 20, 19, 25),
    )
    assert status["label"] == "🔵 MARKET CLOSED"
    assert status["is_current_session"] is False


def test_open_status_for_recent_current_session():
    status = describe_market_status(
        "2026-09-21T10:00:00+05:30",
        datetime(2026, 9, 21, 10, 5),
    )
    assert status["label"] == "🟢 MARKET OPEN"
    assert status["is_current_session"] is True


def test_unknown_timestamp_status():
    status = describe_market_status(None, datetime(2026, 9, 20, 19, 25))
    assert status["label"] == "⚪ DATA STATUS UNKNOWN"
