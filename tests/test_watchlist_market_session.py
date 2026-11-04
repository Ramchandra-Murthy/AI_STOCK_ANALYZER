"""Tests for market-session context exposed by the watchlist."""

from datetime import datetime

import pandas as pd

from scanner.watchlist_scanner import _intraday_context_columns, _market_session_status


def test_market_session_status_uses_shared_calendar():
    assert (
        _market_session_status(datetime.fromisoformat("2026-11-02T10:00:00+05:30"))
        == "OPEN"
    )
    assert (
        _market_session_status(datetime.fromisoformat("2026-11-02T16:00:00+05:30"))
        == "CLOSED"
    )
    assert (
        _market_session_status(datetime.fromisoformat("2026-11-01T10:00:00+05:30"))
        == "CLOSED"
    )


def test_market_session_is_reported_when_intraday_data_is_missing():
    result = _intraday_context_columns(
        None,
        None,
        now=datetime.fromisoformat("2026-11-02T16:00:00+05:30"),
    )
    assert result["Market Session"] == "CLOSED"
    assert result["Context freshness"] == "TIMESTAMP_UNAVAILABLE"


def test_market_session_is_reported_alongside_candle_freshness():
    now = datetime.fromisoformat("2026-11-02T10:00:00+05:30")
    intraday = pd.DataFrame(
        {
            "Open": [100],
            "High": [101],
            "Low": [99],
            "Close": [100],
            "Volume": [10],
        },
        index=[pd.Timestamp("2026-11-02T09:59:00+05:30")],
    )
    result = _intraday_context_columns(intraday, None, now=now)
    assert result["Market Session"] == "OPEN"
    assert result["Context freshness"] == "FRESH"
