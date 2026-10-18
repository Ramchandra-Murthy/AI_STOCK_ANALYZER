from datetime import date

import pandas as pd

from services.market_data_status import describe_daily_history


def test_recent_daily_history_reports_source_and_timestamp():
    history = pd.DataFrame({"Close": [100]}, index=pd.to_datetime(["2026-10-16"]))
    history.attrs["data_source"] = "test-provider"
    history.attrs["last_bar_timestamp"] = "2026-10-16T00:00:00"

    result = describe_daily_history(history, today=date(2026, 10, 18))

    assert result == {
        "status": "RECENT",
        "source": "test-provider",
        "timestamp": "2026-10-16",
    }


def test_old_daily_history_is_marked_stale():
    history = pd.DataFrame({"Close": [100]}, index=pd.to_datetime(["2026-10-10"]))

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
