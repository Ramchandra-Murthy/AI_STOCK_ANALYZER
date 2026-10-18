from datetime import date

import pandas as pd

from services.market_data_status import describe_daily_history


def test_market_data_status_controls_recommendation_verification():
    recent = pd.DataFrame({"Close": [100]}, index=pd.to_datetime(["2026-10-16"]))
    recent.attrs["data_source"] = "test-provider"
    recent.attrs["last_bar_timestamp"] = "2026-10-16T00:00:00"
    stale = pd.DataFrame({"Close": [100]}, index=pd.to_datetime(["2026-10-10"]))

    assert describe_daily_history(recent, today=date(2026, 10, 18))["status"] == "RECENT"
    assert describe_daily_history(stale, today=date(2026, 10, 18))["status"] == "STALE"
    assert describe_daily_history(pd.DataFrame(), today=date(2026, 10, 18))["status"] == "UNKNOWN"
