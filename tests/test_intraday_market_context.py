"""Tests for intraday market-context metrics."""

from datetime import datetime, timedelta

import pandas as pd

from services.intraday_market_context import intraday_market_context


def _candles() -> pd.DataFrame:
    start = datetime.fromisoformat("2026-11-02T09:15:00+05:30")
    frame = pd.DataFrame(
        [
            {"Open": 105, "High": 108, "Low": 104, "Close": 107, "Volume": 1000},
            {"Open": 107, "High": 110, "Low": 106, "Close": 109, "Volume": 2000},
        ]
    )
    frame.index = [start, start + timedelta(minutes=1)]
    return frame


def test_calculates_gap_intraday_move_volume_and_turnover_context():
    result = intraday_market_context(
        _candles(),
        previous_close=100,
        average_daily_volume=10000,
        average_daily_turnover=1_000_000,
    )
    assert result["Gap %"] == 5.0
    assert result["Intraday change %"] == 3.81
    assert result["Session volume"] == 3000
    assert result["Cumulative RVOL"] == 0.3
    assert result["Session turnover"] == 325000
    assert result["Turnover ratio"] == 0.325
    assert result["Context status"] == "OK"


def test_missing_baselines_return_none_not_fake_values():
    result = intraday_market_context(_candles())
    assert result["Gap %"] is None
    assert result["Cumulative RVOL"] is None
    assert result["Turnover ratio"] is None


def test_invalid_ohlcv_rows_are_excluded():
    frame = _candles()
    frame.iloc[0, frame.columns.get_loc("High")] = 1
    result = intraday_market_context(frame, previous_close=100)
    assert result["Session volume"] == 2000


def test_empty_or_missing_columns_return_empty_result():
    assert intraday_market_context(pd.DataFrame()) == {}
    assert intraday_market_context(pd.DataFrame({"Close": [10]})) == {}
