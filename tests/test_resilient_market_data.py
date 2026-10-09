from __future__ import annotations

import pandas as pd

from services import resilient_market_data as market_data


def _frame() -> pd.DataFrame:
    index = pd.date_range("2026-10-05", periods=3, freq="min")
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0],
            "High": [101.0, 102.0, 103.0],
            "Low": [99.0, 100.0, 101.0],
            "Close": [100.5, 101.5, 102.5],
            "Volume": [1000, 1100, 1200],
        },
        index=index,
    )


def test_download_symbol_frames_recovers_missing_symbols(monkeypatch) -> None:
    def fake_batch(tickers, **_kwargs):
        return (
            pd.concat(
                {"AAA.NS": _frame()},
                axis=1,
            )
            if "AAA.NS" in tickers
            else pd.DataFrame()
        )

    monkeypatch.setattr(market_data, "_download_batch", fake_batch)
    monkeypatch.setattr(market_data, "_download_single", lambda ticker, **_: _frame())

    frames, missing = market_data.download_symbol_frames(
        ["AAA.NS", "BBB.NS"],
        period="5d",
        interval="1m",
        batch_size=10,
    )

    assert set(frames) == {"AAA.NS", "BBB.NS"}
    assert missing == []


def test_download_market_frames_reports_unresolved_symbols(monkeypatch) -> None:
    monkeypatch.setattr(
        market_data,
        "_download_batch",
        lambda *_args, **_kwargs: pd.DataFrame(),
    )
    monkeypatch.setattr(
        market_data,
        "_download_single",
        lambda *_args, **_kwargs: pd.DataFrame(),
    )

    frames, diagnostics = market_data.download_market_frames(
        ["AAA.NS", "BBB.NS"],
        period="5d",
        interval="1m",
    )

    assert frames == {}
    assert diagnostics["requested"] == 2
    assert diagnostics["usable"] == 0
    assert diagnostics["coverage_pct"] == 0.0
    assert diagnostics["complete"] is False
    assert diagnostics["missing"] == ["AAA.NS", "BBB.NS"]
