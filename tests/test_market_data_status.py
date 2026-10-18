from datetime import date

import pandas as pd

from services.market_data_status import describe_daily_history


def _history(day, source=None):
    history = pd.DataFrame({"Close": [100]}, index=pd.to_datetime([day]))
    if source:
        history.attrs["data_source"] = source
    history.attrs["last_bar_timestamp"] = f"{day}T00:00:00"
    return history


def test_recent_daily_history_reports_source_and_timestamp():
    history = _history("2026-10-16", "test-provider")

    result = describe_daily_history(history, today=date(2026, 10, 18))

    assert result == {
        "status": "RECENT",
        "source": "test-provider",
        "timestamp": "2026-10-16",
        "is_verified_live": False,
    }


def test_old_daily_history_is_marked_stale_by_trading_days():
    history = _history("2026-10-09")

    result = describe_daily_history(history, today=date(2026, 10, 18))

    assert result["status"] == "STALE"


def test_missing_timestamp_is_unknown():
    history = pd.DataFrame({"Close": [100]}, index=["not-a-date"])

    result = describe_daily_history(history, today=date(2026, 10, 18))

    assert result["status"] == "UNKNOWN"
    assert result["timestamp"] == "Unknown"


def test_empty_history_is_unknown():
    result = describe_daily_history(pd.DataFrame(), today=date(2026, 10, 18))

    assert result["status"] == "UNKNOWN"


def test_weekend_daily_candle_is_unknown():
    history = _history("2026-10-18")

    result = describe_daily_history(history, today=date(2026, 10, 18))

    assert result["status"] == "UNKNOWN"
    assert result["is_verified_live"] is False


def test_holiday_daily_candle_is_unknown():
    history = _history("2026-10-20")

    result = describe_daily_history(history, today=date(2026, 10, 20))

    assert result["status"] == "UNKNOWN"


def test_unsupported_calendar_year_is_unknown():
    history = _history("2026-12-31")

    result = describe_daily_history(history, today=date(2027, 1, 4))

    assert result["status"] == "UNKNOWN"


def test_future_timestamp_is_unknown():
    history = _history("2026-10-19")

    result = describe_daily_history(history, today=date(2026, 10, 18))

    assert result["status"] == "UNKNOWN"
    assert result["timestamp"] == "Unknown"


def test_non_scalar_or_invalid_timestamp_is_unknown():
    history = pd.DataFrame({"Close": [100]}, index=["not-a-date"])
    history.attrs["last_bar_timestamp"] = object()

    result = describe_daily_history(history, today=date(2026, 10, 18))

    assert result["status"] == "UNKNOWN"
    assert result["timestamp"] == "Unknown"
    assert result["is_verified_live"] is False


def test_recent_daily_data_is_never_labelled_verified_live():
    history = _history("2026-10-16")

    result = describe_daily_history(history, today=date(2026, 10, 16))

    assert result["status"] == "RECENT"
    assert result["is_verified_live"] is False
