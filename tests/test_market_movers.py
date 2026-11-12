import pandas as pd

from modules.market_movers import (
    _completed_market_mover_frame,
    _extract_frame,
    _ticker,
    _top_table,
    _window_change,
)


def test_ticker_normalization_preserves_exchange_suffix():
    assert _ticker("RELIANCE", "NSE") == "RELIANCE.NS"
    assert _ticker("500325", "BSE") == "500325.BO"
    assert _ticker("TCS.NS", "BSE") == "TCS.NS"


def test_window_change_uses_requested_bar_baseline():
    close = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0])
    assert _window_change(close, 1) == 0.952
    assert _window_change(close, 3) == 2.913
    assert _window_change(close, 8) is None


def test_top_table_separates_gainers_and_losers():
    frame = pd.DataFrame(
        {
            "Symbol": ["A", "B", "C"],
            "Change 5m %": [1.2, -0.8, 0.0],
        }
    )
    assert _top_table(frame, "Change 5m %", True, 10)["Symbol"].tolist() == ["A"]
    assert _top_table(frame, "Change 5m %", False, 10)["Symbol"].tolist() == ["B"]


def test_extract_frame_handles_plain_ohlcv_data():
    frame = pd.DataFrame(
        {
            "Open": [10.0, 11.0],
            "High": [12.0, 12.0],
            "Low": [9.0, 10.0],
            "Close": [11.0, 11.5],
            "Volume": [100, 120],
        }
    )
    result = _extract_frame(frame, "TEST.NS")
    assert set(result.columns) == {"Open", "High", "Low", "Close", "Volume"}
    assert result["Close"].tolist() == [11.0, 11.5]


def test_market_movers_rejects_incomplete_future_duplicate_and_invalid_candles():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    zone = ZoneInfo("Asia/Kolkata")
    frame = pd.DataFrame(
        {
            "Open": [100, 100, 100, 100, 100, 100],
            "High": [102, 102, 102, 102, 100, 102],
            "Low": [99, 99, 99, 99, 99, 99],
            "Close": [100, 101, 102, 103, 101, 100],
            "Volume": [1000, 1100, 1200, 1300, 1400, 1500],
        },
        index=[
            pd.Timestamp("2026-10-19 09:55", tz=zone),
            pd.Timestamp("2026-10-19 09:55", tz=zone),
            pd.Timestamp("2026-10-19 10:00", tz=zone),
            pd.Timestamp("2026-10-19 10:05", tz=zone),
            "invalid timestamp",
            pd.Timestamp("2026-10-19 09:50", tz=zone),
        ],
    )
    frame.iloc[5, frame.columns.get_loc("High")] = 98

    result, rejected = _completed_market_mover_frame(
        frame,
        datetime(2026, 10, 19, 10, 2, 30, tzinfo=zone),
    )

    assert result["Close"].tolist() == [101.0]
    assert rejected == {
        "invalid_timestamps": 1,
        "future_candles": 1,
        "incomplete_candles": 1,
        "duplicate_candles": 1,
        "missing_ohlcv": 0,
        "invalid_ohlcv": 1,
        "missing_ohlcv_columns": 0,
        "stale_symbols": 0,
    }


def test_market_movers_rejects_stale_intraday_history_during_open_session():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    zone = ZoneInfo("Asia/Kolkata")
    index = pd.date_range("2026-10-19 09:15", periods=7, freq="5min", tz=zone)
    frame = pd.DataFrame(
        {"Open": 100, "High": 102, "Low": 99, "Close": 101, "Volume": 1000},
        index=index,
    )

    result, rejected = _completed_market_mover_frame(
        frame,
        datetime(2026, 10, 19, 11, 0, tzinfo=zone),
    )

    assert result.empty
    assert rejected["stale_symbols"] == 1


def test_quote_freshness_marks_old_candle_stale_during_open_session():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from modules.market_movers import _quote_freshness

    now = datetime(2026, 10, 19, 11, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    assert _quote_freshness("2026-10-19 10:40:00 IST", now) == "STALE INTRADAY DATA"


def test_quote_freshness_labels_recent_open_session_candle():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from modules.market_movers import _quote_freshness

    now = datetime(2026, 10, 19, 11, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    assert (
        _quote_freshness("2026-10-19 10:55:00 IST", now) == "CURRENT-SESSION CANDLE · NOT TICK-LIVE"
    )


def test_quote_freshness_labels_weekend_snapshot_as_closed():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from modules.market_movers import _quote_freshness

    now = datetime(2026, 10, 18, 11, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    assert _quote_freshness("2026-10-16 15:25:00 IST", now) == "MARKET CLOSED · LAST AVAILABLE DATA"


def test_market_movers_scan_uses_shared_market_data_service(monkeypatch):
    from modules import market_movers

    index = pd.date_range("2026-11-10 09:15", periods=8, freq="5min", tz="Asia/Kolkata")
    frame = pd.DataFrame(
        {
            "Open": [100.0] * 8,
            "High": [101.0] * 7 + [103.0],
            "Low": [99.0] * 8,
            "Close": [100.0, 100.2, 100.4, 100.6, 100.8, 101.0, 101.2, 102.0],
            "Volume": [1000] * 7 + [3000],
        },
        index=index,
    )
    calls = []

    def fake_download(tickers, **kwargs):
        calls.append((tickers, kwargs))
        return {tickers[0]: frame}, []

    monkeypatch.setattr(market_movers, "download_symbol_frames", fake_download)
    monkeypatch.setattr(market_movers, "_quote_freshness", lambda _value: "TEST")

    result, stats = market_movers._scan_batches([("TEST", "NSE")], 1)

    assert calls[0][0] == ["TEST.NS"]
    assert calls[0][1]["interval"] == "5m"
    assert calls[0][1]["recover_missing"] is True
    assert stats["usable_quotes"] == 1
    assert result.iloc[0]["Symbol"] == "TEST"


def test_market_cap_uses_shared_metadata_service(monkeypatch):
    from modules import market_movers

    calls = []
    monkeypatch.setattr(
        market_movers,
        "get_market_cap",
        lambda ticker, **kwargs: calls.append((ticker, kwargs)) or 123.0,
    )

    assert market_movers._market_cap("TEST.NS") == 123.0
    assert calls == [("TEST.NS", {"cache_ttl_seconds": market_movers.CAP_CACHE_TTL_SECONDS})]


def test_bse_group_uses_official_codes_and_preserves_nse():
    from modules.market_movers import _attach_bse_group

    frame = pd.DataFrame(
        {
            "Ticker": ["500325.BO", "532540.BO", "RELIANCE.NS"],
            "Exchange": ["BSE", "BSE", "NSE"],
        }
    )
    result = _attach_bse_group(frame, {"500325"})
    assert result["BSE Group"].tolist() == ["A", "Other", "N/A"]


def test_bse_group_unavailable_is_not_misclassified():
    from modules.market_movers import _attach_bse_group

    frame = pd.DataFrame(
        {
            "Ticker": ["500325.BO", "RELIANCE.NS"],
            "Exchange": ["BSE", "NSE"],
        }
    )
    result = _attach_bse_group(frame, None)
    assert result["BSE Group"].tolist() == ["Unverified", "N/A"]


def test_market_movers_submits_exchange_universe_in_one_bounded_parallel_call(monkeypatch):
    from modules import market_movers

    index = pd.date_range("2026-11-10 09:15", periods=8, freq="5min", tz="Asia/Kolkata")
    frame = pd.DataFrame(
        {
            "Open": [100.0] * 8,
            "High": [101.0] * 7 + [103.0],
            "Low": [99.0] * 8,
            "Close": [100.0, 100.2, 100.4, 100.6, 100.8, 101.0, 101.2, 102.0],
            "Volume": [1000] * 8,
        },
        index=index,
    )
    calls = []
    monkeypatch.setattr(market_movers, "BATCH_SIZE", 2)
    monkeypatch.setattr(market_movers, "_quote_freshness", lambda _value: "TEST")

    def fake_download(tickers, **kwargs):
        calls.append((list(tickers), kwargs))
        return {ticker: frame for ticker in tickers}, []

    monkeypatch.setattr(market_movers, "download_symbol_frames", fake_download)

    result, stats = market_movers._scan_batches([("AAA", "NSE"), ("BBB", "NSE"), ("CCC", "BSE")], 0)

    assert len(calls) == 1
    assert calls[0][0] == ["AAA.NS", "BBB.NS", "CCC.BO"]
    assert calls[0][1]["batch_size"] == 2
    assert calls[0][1]["max_workers"] == 4
    assert stats["batches"] == 2
    assert stats["usable_quotes"] == 3
    assert set(result["Ticker"]) == {"AAA.NS", "BBB.NS", "CCC.BO"}
