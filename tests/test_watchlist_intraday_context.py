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


AS_OF = datetime.fromisoformat("2026-11-02T09:18:00+05:30")


def test_watchlist_intraday_context_uses_prior_daily_baselines():
    from scanner.watchlist_scanner import _intraday_context_columns

    intraday, daily = _frames()
    result = _intraday_context_columns(intraday, daily, now=AS_OF)

    assert result["Gap %"] == 2.941
    assert result["Intraday change %"] == 3.81
    assert result["Session volume"] == 3000
    assert result["Cumulative RVOL"] == 0.273
    assert result["Turnover ratio"] == 0.292
    assert result["Cumulative RVOL basis"] == "Not time-of-day normalized"
    assert result["Context status"] == "OK"


def test_watchlist_intraday_context_fails_closed_when_data_missing():
    from scanner.watchlist_scanner import _intraday_context_columns

    result = _intraday_context_columns(pd.DataFrame(), pd.DataFrame())

    assert result["Gap %"] is None
    assert result["Cumulative RVOL"] is None
    assert result["Turnover ratio"] is None
    assert result["Context status"] == "INTRADAY CONTEXT UNAVAILABLE"


def test_watchlist_context_withholds_metrics_when_ohlcv_is_invalid():
    from scanner.watchlist_scanner import _intraday_context_columns

    intraday, daily = _frames()
    intraday.loc[intraday.index[0], "Volume"] = -1

    result = _intraday_context_columns(intraday, daily, now=AS_OF)

    assert result["Context status"] == "INVALID INTRADAY DATA"
    assert result["Session volume"] is None
    assert "invalid OHLCV: 1" in result["Context rejection reason"]


def test_watchlist_context_excludes_same_session_daily_candle():
    from scanner.watchlist_scanner import _intraday_context_columns

    intraday, daily = _frames()
    same_day = pd.DataFrame(
        [{"Close": 999, "Volume": 999999}],
        index=pd.DatetimeIndex(["2026-11-02"]),
    )
    daily = pd.concat([daily, same_day])

    result = _intraday_context_columns(intraday, daily, now=AS_OF)

    assert result["Gap %"] == 2.941
    assert result["Cumulative RVOL"] == 0.273


def test_intraday_context_deduplicates_timestamps_without_double_counting():
    from services.intraday_market_context import intraday_market_context

    timestamp = pd.Timestamp("2026-11-02T09:15:00+05:30")
    intraday = pd.DataFrame(
        [
            {"Open": 105, "High": 108, "Low": 104, "Close": 107, "Volume": 1000},
            {"Open": 105, "High": 107, "Low": 104, "Close": 106, "Volume": 2000},
        ],
        index=[timestamp, timestamp],
    )

    result = intraday_market_context(intraday, previous_close=102)

    assert result["Session volume"] == 2000
    assert result["Last price"] == 106
    assert result["Intraday change %"] == 0.952


def test_intraday_context_filters_invalid_ohlcv_rows():
    from services.intraday_market_context import intraday_market_context

    timestamp = pd.Timestamp("2026-11-02T09:15:00+05:30")
    intraday = pd.DataFrame(
        [
            {"Open": 105, "High": 108, "Low": 104, "Close": 107, "Volume": 1000},
            {"Open": 105, "High": 103, "Low": 104, "Close": 107, "Volume": 9000},
            {"Open": 105, "High": 108, "Low": 104, "Close": 107, "Volume": -10},
            {"Open": "bad", "High": 108, "Low": 104, "Close": 107, "Volume": 9000},
        ],
        index=[
            timestamp,
            timestamp + pd.Timedelta(minutes=1),
            timestamp + pd.Timedelta(minutes=2),
            timestamp + pd.Timedelta(minutes=3),
        ],
    )

    result = intraday_market_context(intraday, previous_close=102)

    assert result["Session volume"] == 1000
    assert result["Last price"] == 107
    assert result["Context status"] == "OK"


def test_intraday_context_invalid_baselines_do_not_create_relative_metrics():
    from services.intraday_market_context import intraday_market_context

    intraday, _ = _frames()
    result = intraday_market_context(
        intraday,
        previous_close=float("nan"),
        average_daily_volume=0,
        average_daily_turnover=float("inf"),
    )

    assert result["Gap %"] is None
    assert result["Cumulative RVOL"] is None
    assert result["Turnover ratio"] is None
    assert result["Session volume"] == 3000
