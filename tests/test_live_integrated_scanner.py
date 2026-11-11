import numpy as np
import pandas as pd

from engine.live_integrated_scanner import scan_integrated_tickers


def _history(rows: int = 60) -> pd.DataFrame:
    close = np.linspace(100.0, 130.0, rows)
    return pd.DataFrame(
        {
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
        },
        index=pd.date_range("2026-01-01", periods=rows, freq="D"),
    )


def test_scan_integrated_tickers_returns_latest_signal() -> None:
    history = {"RELIANCE.NS": _history()}

    def downloader(tickers, *, period, interval):
        del tickers, period, interval
        return pd.concat(history, axis=1)

    result = scan_integrated_tickers(
        ["RELIANCE.NS"],
        fast_period=5,
        slow_period=20,
        downloader=downloader,
    )

    assert list(result.columns) == [
        "Ticker",
        "Close",
        "Regime",
        "Regime Score",
        "Edge Signal",
        "Direction",
    ]
    assert result.iloc[0]["Ticker"] == "RELIANCE.NS"
    assert result.iloc[0]["Edge Signal"] == 1.0
    assert result.iloc[0]["Direction"] == "LONG"


def test_scan_integrated_tickers_skips_short_history() -> None:
    short = {"RELIANCE.NS": _history(10)}

    def downloader(tickers, *, period, interval):
        del tickers, period, interval
        return pd.concat(short, axis=1)

    result = scan_integrated_tickers(
        ["RELIANCE.NS"],
        fast_period=5,
        slow_period=20,
        downloader=downloader,
    )

    assert result.empty


def test_scan_integrated_tickers_deduplicates_symbols() -> None:
    history = {"RELIANCE.NS": _history()}

    def downloader(tickers, *, period, interval):
        assert tickers == ["RELIANCE.NS"]
        del period, interval
        return pd.concat(history, axis=1)

    result = scan_integrated_tickers(
        [" reliance.ns ", "RELIANCE.NS"],
        fast_period=5,
        slow_period=20,
        downloader=downloader,
    )

    assert len(result) == 1


def test_default_download_uses_shared_resilient_market_data(monkeypatch) -> None:
    import engine.live_integrated_scanner as scanner

    expected = _history()
    calls = {}

    def shared_download(tickers, **kwargs):
        calls["tickers"] = list(tickers)
        calls["kwargs"] = kwargs
        return {"RELIANCE.NS": expected}, []

    monkeypatch.setattr(scanner, "download_symbol_frames", shared_download)

    result = scanner._download(["RELIANCE.NS"], period="6mo", interval="1d")

    assert result.equals(pd.concat({"RELIANCE.NS": expected}, axis=1))
    assert calls["tickers"] == ["RELIANCE.NS"]
    assert calls["kwargs"]["timeout"] == 10
    assert calls["kwargs"]["recover_missing"] is True
