"""Regression tests for the unusual-activity scanner."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from scanner import unusual_activity

AS_OF = datetime(2026, 10, 16, 9, 45, tzinfo=ZoneInfo("Asia/Kolkata"))


def _two_session_frame(latest_volume: float, latest_close: float) -> pd.DataFrame:
    previous = pd.date_range("2026-10-15 09:15", periods=4, freq="5min")
    current = pd.date_range("2026-10-16 09:15", periods=4, freq="5min")
    index = previous.append(current)
    return pd.DataFrame(
        {
            "Open": [100.0] * 8,
            "High": [106.0] * 8,
            "Low": [99.0] * 8,
            "Close": [100.0] * 7 + [latest_close],
            "Volume": [100.0] * 7 + [latest_volume],
        },
        index=index,
    )


def _fake_download(frame_for_each_ticker: pd.DataFrame | None):
    def fake(tickers, **_kwargs):
        frames = (
            {ticker: frame_for_each_ticker.copy() for ticker in tickers}
            if frame_for_each_ticker is not None
            else {}
        )
        return frames, {"missing": [] if frames else list(tickers)}

    return fake


def test_scan_returns_rows_when_data_is_available(monkeypatch) -> None:
    monkeypatch.setattr(
        unusual_activity,
        "download_market_frames",
        _fake_download(_two_session_frame(latest_volume=1000.0, latest_close=105.0)),
    )

    result = unusual_activity.scan_unusual_activity(
        limit=5, cap_category="Large cap", exchange_category="NSE", as_of=AS_OF
    )

    assert not result.empty
    assert len(result) <= 5
    assert (result["Relative volume"] >= 1.5).all()
    assert (result["Session change %"] > 0).all()
    assert result.attrs["scan_stats"]["usable_count"] > 0


def test_scan_skips_symbols_without_a_volume_spike(monkeypatch) -> None:
    monkeypatch.setattr(
        unusual_activity,
        "download_market_frames",
        _fake_download(_two_session_frame(latest_volume=100.0, latest_close=105.0)),
    )

    result = unusual_activity.scan_unusual_activity(
        limit=5, cap_category="Large cap", exchange_category="NSE", as_of=AS_OF
    )

    assert result.empty


def test_scan_handles_empty_download_without_raising(monkeypatch) -> None:
    monkeypatch.setattr(unusual_activity, "download_market_frames", _fake_download(None))

    result = unusual_activity.scan_unusual_activity(
        limit=5, cap_category="Large cap", exchange_category="NSE", as_of=AS_OF
    )

    assert result.empty
    assert result.attrs["scan_stats"]["empty_chunks"] > 0


def test_completed_activity_frame_rejects_partial_future_duplicate_and_invalid_bars() -> None:
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
            pd.Timestamp("2026-10-16 09:55", tz=zone),
            pd.Timestamp("2026-10-16 09:55", tz=zone),
            pd.Timestamp("2026-10-16 10:00", tz=zone),
            pd.Timestamp("2026-10-16 10:05", tz=zone),
            "invalid timestamp",
            pd.Timestamp("2026-10-16 09:50", tz=zone),
        ],
    )
    frame.iloc[5, frame.columns.get_loc("High")] = 98

    result, rejected = unusual_activity._completed_activity_frame(
        frame,
        datetime(2026, 10, 16, 10, 2, 30, tzinfo=zone),
    )

    assert result["Close"].tolist() == [101.0]
    assert rejected == {
        "incomplete_candles": 1,
        "future_candles": 1,
        "duplicate_candles": 1,
        "invalid_timestamps": 1,
        "missing_ohlcv": 0,
        "invalid_ohlcv": 1,
        "stale_symbols": 0,
        "missing_ohlcv_columns": 0,
    }
