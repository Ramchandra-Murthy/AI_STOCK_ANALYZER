import pandas as pd

from modules.scanner import _live_intraday_rows


def test_live_intraday_rows_requires_explicit_live_status_timestamp_and_price() -> None:
    frame = pd.DataFrame(
        [
            {
                "Symbol": "RELIANCE",
                "Tick Live": True,
                "Observation Status": "LIVE QUOTE",
                "Observed At": "2026-10-26T09:20:00+05:30",
                "Latest Observation Price": 1500.0,
            },
            {
                "Symbol": "TCS",
                "Tick Live": False,
                "Observation Status": "LIVE QUOTE",
                "Observed At": "2026-10-26T09:20:00+05:30",
                "Latest Observation Price": 3000.0,
            },
            {
                "Symbol": "INFY",
                "Tick Live": True,
                "Observation Status": "MARKET DATA STATUS UNAVAILABLE",
                "Observed At": "2026-10-26T09:20:00+05:30",
                "Latest Observation Price": 1500.0,
            },
            {
                "Symbol": "WIPRO",
                "Tick Live": True,
                "Observation Status": "LIVE QUOTE",
                "Observed At": "UNKNOWN",
                "Latest Observation Price": 500.0,
            },
            {
                "Symbol": "HDFCBANK",
                "Tick Live": True,
                "Observation Status": "LIVE QUOTE",
                "Observed At": "2026-10-26T09:20:00+05:30",
                "Latest Observation Price": 0.0,
            },
        ]
    )

    result = _live_intraday_rows(frame)

    assert result["Symbol"].tolist() == ["RELIANCE"]


def test_live_intraday_rows_fails_closed_when_observation_columns_are_missing() -> None:
    frame = pd.DataFrame([{"Symbol": "RELIANCE", "Price": 1500.0}])

    result = _live_intraday_rows(frame)

    assert result.empty
    assert list(result.columns) == list(frame.columns)
