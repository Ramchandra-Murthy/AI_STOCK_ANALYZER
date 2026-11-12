from datetime import datetime

import pandas as pd

from scanner import watchlist_scanner


def _analysis_result():
    return {
        "last": {"Close": 109.0, "RSI_14": 55.0, "MACD": 1.2, "ATR": 2.1},
        "signal": {
            "Score": 7,
            "Confidence": 0.8,
            "Recommendation": "WATCH",
            "MarketObservation": {},
        },
        "trend": {"Trend": "UPTREND"},
    }


def test_watchlist_scan_reports_requested_returned_and_failed_symbols(monkeypatch):
    timestamp = pd.Timestamp("2026-11-02T09:15:00+05:30")
    intraday = pd.DataFrame(
        [{"Open": 100, "High": 101, "Low": 99, "Close": 100, "Volume": 1000}],
        index=[timestamp],
    )
    daily = pd.DataFrame(
        [{"Close": 100, "Volume": 10000}],
        index=[pd.Timestamp("2026-10-30")],
    )

    def fake_download(tickers, **kwargs):
        frames = {"AAA.NS": intraday if kwargs["interval"] == "1m" else daily}
        return frames, [ticker for ticker in tickers if ticker not in frames]

    def fake_analysis(ticker):
        if ticker == "BBB.BO":
            raise ValueError("provider unavailable")
        return _analysis_result()

    monkeypatch.setattr(watchlist_scanner, "download_symbol_frames", fake_download)
    monkeypatch.setattr(watchlist_scanner, "analyze_stock", fake_analysis)

    result = watchlist_scanner.scan_watchlist(
        ["AAA.NS", "AAA", "", "BBB.BO", "BBB.BO"],
        now=datetime.fromisoformat("2026-11-02T09:18:00+05:30"),
    )

    stats = result.attrs["scan_stats"]
    assert stats["symbols_requested"] == 5
    assert stats["unique_tickers_requested"] == 2
    assert stats["duplicate_entries_removed"] == 2
    assert stats["invalid_entries"] == 1
    assert stats["intraday_frames_returned"] == 1
    assert stats["daily_frames_returned"] == 1
    assert stats["intraday_symbols_missing"] == ["BBB.BO"]
    assert stats["daily_symbols_missing"] == ["BBB.BO"]
    assert stats["analysis_attempted"] == 2
    assert stats["analysis_completed"] == 1
    assert stats["analysis_failed"] == 1
    assert stats["analysis_failed_symbols"] == ["BBB.BO"]


def test_watchlist_scan_keeps_coverage_when_no_symbol_can_be_analyzed(monkeypatch):
    monkeypatch.setattr(
        watchlist_scanner, "analyze_stock", lambda _ticker: (_ for _ in ()).throw(ValueError())
    )
    monkeypatch.setattr(
        watchlist_scanner,
        "download_symbol_frames",
        lambda tickers, **_kwargs: ({}, tickers),
    )

    result = watchlist_scanner.scan_watchlist(["AAA", "BBB"])

    assert result.empty
    assert result.attrs["scan_stats"]["analysis_attempted"] == 2
    assert result.attrs["scan_stats"]["analysis_failed"] == 2
