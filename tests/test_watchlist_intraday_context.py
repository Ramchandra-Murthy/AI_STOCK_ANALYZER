from datetime import datetime, timedelta

import pandas as pd


def _frames():
    session = datetime.fromisoformat("2026-11-02T09:15:00+05:30")
    intraday = pd.DataFrame(
        [
            {"Open": 105, "High": 108, "Low": 104, "Close": 107, "Volume": 1000},
            {"Open": 107, "High": 110, "Low": 106, "Close": 109, "Volume": 2000},
        ],
        index=[session, session + timedelta(minutes=1)],
    )
    daily = pd.DataFrame(
        [
            {"Close": 100, "Volume": 10000},
            {"Close": 102, "Volume": 12000},
        ],
        index=pd.DatetimeIndex(["2026-10-29", "2026-10-30"]),
    )
    return intraday, daily


def test_watchlist_intraday_context_uses_prior_daily_baselines():
    from scanner.watchlist_scanner import _intraday_context_columns

    intraday, daily = _frames()
    result = _intraday_context_columns(intraday, daily)

    assert result["Gap %"] == 5.0
    assert result["Intraday change %"] == 3.81
    assert result["Session volume"] == 3000
    assert result["Cumulative RVOL"] == 0.273
    assert result["Turnover ratio"] == 0.268
    assert result["Cumulative RVOL basis"] == "Not time-of-day normalized"
    assert result["Context status"] == "OK"


def test_watchlist_intraday_context_fails_closed_when_data_missing():
    from scanner.watchlist_scanner import _intraday_context_columns

    result = _intraday_context_columns(pd.DataFrame(), pd.DataFrame())

    assert result["Gap %"] is None
    assert result["Cumulative RVOL"] is None
    assert result["Turnover ratio"] is None
    assert result["Context status"] == "INTRADAY CONTEXT UNAVAILABLE"


def test_watchlist_context_excludes_same_session_daily_candle():
    from scanner.watchlist_scanner import _intraday_context_columns

    intraday, daily = _frames()
    same_day = pd.DataFrame(
        [{"Close": 999, "Volume": 999999}],
        index=pd.DatetimeIndex(["2026-11-02"]),
    )
    daily = pd.concat([daily, same_day])

    result = _intraday_context_columns(intraday, daily)

    assert result["Gap %"] == 5.0
    assert result["Cumulative RVOL"] == 0.273
