import numpy as np
import pandas as pd

from scanner.price_jump import _candle_settings, calculate_price_jump


def _ohlcv_frame(index, closes, volumes):
    return pd.DataFrame(
        {
            "Open": closes,
            "High": closes,
            "Low": closes,
            "Close": closes,
            "Volume": volumes,
        },
        index=index,
    )


def test_calculate_price_jump_uses_same_session_bars():
    index = pd.to_datetime(
        [
            "2026-09-17 15:25",
            "2026-09-18 09:15",
            "2026-09-18 09:20",
        ]
    )
    frame = _ohlcv_frame(index, [100.0, 100.0, 101.5], [1000, 1200, 1800])

    result = calculate_price_jump(
        frame,
        lookback_bars=1,
        jump_percent=1.0,
        interval_minutes=5,
        as_of=pd.Timestamp("2026-09-18 09:32", tz="Asia/Kolkata").to_pydatetime(),
    )

    assert result is not None
    assert result["intraday_pct"] == 1.5
    assert result["day_pct"] == 1.5
    assert result["qualifies"] == 1.0
    assert result["volume"] == 1800.0


def test_calculate_price_jump_rejects_insufficient_bars():
    frame = _ohlcv_frame(pd.to_datetime(["2026-09-18 09:15"]), [100.0], [1000])

    assert (
        calculate_price_jump(
            frame,
            lookback_bars=1,
            as_of=pd.Timestamp("2026-09-18 09:17", tz="Asia/Kolkata").to_pydatetime(),
        )
        is None
    )


def test_calculate_price_jump_does_not_cross_session_boundary():
    index = pd.to_datetime(["2026-09-17 15:25", "2026-09-18 09:15"])
    frame = _ohlcv_frame(index, [100.0, 105.0], [1000, 2000])

    assert (
        calculate_price_jump(
            frame,
            lookback_bars=1,
            as_of=pd.Timestamp("2026-09-18 09:17", tz="Asia/Kolkata").to_pydatetime(),
        )
        is None
    )


def test_calculate_price_jump_supports_short_window_bar_count():
    index = pd.date_range("2026-09-18 09:15", periods=4, freq="1min")
    frame = _ohlcv_frame(index, [100.0, 100.2, 100.5, 101.5], [1000, 1100, 1200, 2000])

    result = calculate_price_jump(
        frame,
        lookback_bars=3,
        jump_percent=1.0,
        as_of=pd.Timestamp("2026-09-18 09:20", tz="Asia/Kolkata").to_pydatetime(),
    )

    assert result is not None
    assert round(result["intraday_pct"], 2) == 1.5
    assert result["qualifies"] == 1.0


def test_calculate_price_jump_supports_one_minute_window():
    index = pd.date_range("2026-09-18 09:15", periods=2, freq="1min")
    frame = _ohlcv_frame(index, [100.0, 101.0], [1000, 1800])

    result = calculate_price_jump(
        frame,
        lookback_bars=1,
        jump_percent=0.5,
        as_of=pd.Timestamp("2026-09-18 09:18", tz="Asia/Kolkata").to_pydatetime(),
    )

    assert result is not None
    assert result["intraday_pct"] == 1.0
    assert result["day_pct"] == 1.0
    assert result["qualifies"] == 1.0


def test_calculate_price_jump_rejects_infinite_prices_and_volumes():
    index = pd.date_range("2026-09-18 09:15", periods=3, freq="1min")
    frame = _ohlcv_frame(index, [100.0, np.inf, 102.0], [1000.0, 1200.0, np.inf])

    result = calculate_price_jump(
        frame,
        lookback_bars=1,
        as_of=pd.Timestamp("2026-09-18 09:19", tz="Asia/Kolkata").to_pydatetime(),
    )

    assert result is None


def test_calculate_price_jump_rejects_non_positive_prices_and_negative_volume():
    index = pd.date_range("2026-09-18 09:15", periods=3, freq="1min")
    frame = _ohlcv_frame(index, [100.0, 0.0, 102.0], [1000.0, -10.0, 1500.0])

    result = calculate_price_jump(
        frame,
        lookback_bars=1,
        as_of=pd.Timestamp("2026-09-18 09:19", tz="Asia/Kolkata").to_pydatetime(),
    )

    assert result is None


def test_calculate_price_jump_never_scores_a_forming_one_minute_bar():
    index = pd.date_range("2026-09-18 09:15", periods=2, freq="1min")
    frame = _ohlcv_frame(index, [100.0, 110.0], [1000, 3000])

    result = calculate_price_jump(
        frame,
        lookback_bars=1,
        as_of=pd.Timestamp("2026-09-18 09:16:30", tz="Asia/Kolkata").to_pydatetime(),
    )

    assert result is None


def test_candle_settings_use_one_minute_for_short_windows():
    assert _candle_settings(1) == ("1m", 1)
    assert _candle_settings(2) == ("1m", 2)
    assert _candle_settings(3) == ("1m", 3)


def test_candle_settings_use_five_minute_for_longer_windows():
    assert _candle_settings(5) == ("5m", 1)
    assert _candle_settings(10) == ("5m", 2)
