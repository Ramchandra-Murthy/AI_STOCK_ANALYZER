"""Tests for the intraday scanner's shared market-data boundary."""

import pandas as pd

import modules.intraday as intraday


def test_intraday_download_uses_shared_market_data_controls(monkeypatch) -> None:
    calls: dict[str, object] = {}
    frame = pd.DataFrame({"Close": [100.0]}, index=pd.DatetimeIndex(["2026-11-11 09:15:00"]))

    def fake_download(tickers, **kwargs):
        calls["tickers"] = tickers
        calls.update(kwargs)
        return {"RELIANCE.NS": frame}, []

    monkeypatch.setattr(intraday, "download_symbol_frames", fake_download)

    frames, missing = intraday._download_intraday_frames(["RELIANCE.NS"], "1m")

    assert frames["RELIANCE.NS"].equals(frame)
    assert missing == []
    assert calls["tickers"] == ["RELIANCE.NS"]
    assert calls["period"] == "5d"
    assert calls["interval"] == "1m"
    assert calls["batch_size"] == intraday.LIVE_BOARD_CHUNK_SIZE
    assert calls["timeout"] == 10
    assert calls["recover_missing"] is False


def test_intraday_download_can_recover_missing_single_symbol(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_download(tickers, **kwargs):
        calls.update(kwargs)
        return {}, list(tickers)

    monkeypatch.setattr(intraday, "download_symbol_frames", fake_download)

    frames, missing = intraday._download_intraday_frames(["TCS.NS"], "5m", recover_missing=True)

    assert frames == {}
    assert missing == ["TCS.NS"]
    assert calls["recover_missing"] is True
