"""End-to-end integration tests for watchlist intraday context columns."""

from datetime import datetime, timedelta

import pandas as pd


def _analysis_result():
    last = {
        "Close": 109.0,
        "RSI_14": 55.0,
        "MACD": 1.2,
        "ATR": 2.1,
    }
    signal = {
        "Score": 7,
        "Confidence": 0.8,
        "Recommendation": "WATCH",
        "MarketObservation": {
            "price": 109.0,
            "observed_at": "2026-11-02T09:16:00+05:30",
            "frequency": "1m",
            "session_status": "MARKET OPEN",
            "is_tick_live": False,
        },
    }
    return {"last": last, "signal": signal, "trend": {"Trend": "UPTREND"}}


def _market_frames():
    start = datetime.fromisoformat("2026-11-02T09:15:00+05:30")
    intraday = pd.DataFrame(
        [
            {"Open": 105, "High": 108, "Low": 104, "Close": 107, "Volume": 1000},
            {"Open": 107, "High": 110, "Low": 106, "Close": 109, "Volume": 2000},
        ],
        index=[start, start + timedelta(minutes=1)],
    )
    daily = pd.DataFrame(
        [
            {"Close": 100, "Volume": 10000},
            {"Close": 102, "Volume": 12000},
        ],
        index=pd.DatetimeIndex(["2026-10-29", "2026-10-30"]),
    )
    return intraday, daily


def test_scan_watchlist_includes_intraday_context_without_changing_analysis(
    monkeypatch,
):
    from scanner import watchlist_scanner

    intraday, daily = _market_frames()
    monkeypatch.setattr(
        watchlist_scanner,
        "download_symbol_frames",
        lambda tickers, **kwargs: (
            ({"ABC.NS": intraday} if kwargs["interval"] == "1m" else {"ABC.NS": daily}),
            {},
        ),
    )
    monkeypatch.setattr(watchlist_scanner, "analyze_stock", lambda ticker: _analysis_result())

    result = watchlist_scanner.scan_watchlist(
        ["ABC"], now=datetime.fromisoformat("2026-11-02T09:18:00+05:30")
    )

    assert len(result) == 1
    row = result.iloc[0]
    assert row["Symbol"] == "ABC"
    assert row["Price"] == 109.0
    assert row["AI Score"] == 7
    assert row["Recommendation"] == "WATCH"
    assert row["Gap %"] == 2.941
    assert row["Intraday change %"] == 3.81
    assert row["Session volume"] == 3000
    assert row["Cumulative RVOL"] == 0.273
    assert row["Context status"] == "OK"
    assert row["Context freshness"] == "FRESH"
    assert row["Cumulative RVOL basis"] == "Not time-of-day normalized"


def test_scan_watchlist_keeps_analysis_when_intraday_download_fails(monkeypatch):
    from scanner import watchlist_scanner

    def fail_download(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(watchlist_scanner, "download_symbol_frames", fail_download)
    monkeypatch.setattr(watchlist_scanner, "analyze_stock", lambda ticker: _analysis_result())

    result = watchlist_scanner.scan_watchlist(["ABC"])

    assert len(result) == 1
    row = result.iloc[0]
    assert row["Price"] == 109.0
    assert row["AI Score"] == 7
    assert row["Recommendation"] == "WATCH"
    assert row["Gap %"] is None
    assert row["Cumulative RVOL"] is None
    assert row["Turnover ratio"] is None
    assert row["Context status"] == "INTRADAY CONTEXT UNAVAILABLE"
    assert row["Context freshness"] == "TIMESTAMP_UNAVAILABLE"


def test_watchlist_context_freshness_is_fresh_at_evaluation_time():
    from scanner.watchlist_scanner import _intraday_context_columns

    intraday, daily = _market_frames()
    evaluation_time = datetime.fromisoformat("2026-11-02T09:17:00+05:30")

    result = _intraday_context_columns(intraday, daily, now=evaluation_time)

    assert result["Context freshness"] == "FRESH"


def test_watchlist_context_freshness_flags_future_candle_timestamp():
    from scanner.watchlist_scanner import _intraday_context_columns

    intraday, daily = _market_frames()
    evaluation_time = datetime.fromisoformat("2026-11-02T09:15:30+05:30")

    result = _intraday_context_columns(intraday, daily, now=evaluation_time)

    assert result["Context freshness"] == "FUTURE_TIMESTAMP"
    assert result["Context status"] == "INVALID INTRADAY DATA"
    assert result["Intraday change %"] is None
