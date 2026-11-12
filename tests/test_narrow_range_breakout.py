import pandas as pd

from scanner.day_trading_strategy import (
    analyze_narrow_range_breakout,
    classify_narrow_range_breakout,
)


def _frame(ranges):
    index = pd.date_range("2026-10-01 09:15", periods=len(ranges), freq="5min")
    closes = [100.0 + i * 0.2 for i in range(len(ranges))]
    return pd.DataFrame(
        {
            "Open": closes,
            "High": [close + width / 2 for close, width in zip(closes, ranges, strict=True)],
            "Low": [close - width / 2 for close, width in zip(closes, ranges, strict=True)],
            "Close": closes,
            "Volume": [1000] * len(ranges),
        },
        index=index,
    )


def _after_latest_candle(frame, *, minutes=10):
    return (frame.index[-1] + pd.Timedelta(minutes=minutes)).to_pydatetime()


def test_detects_nr4_with_next_bar_trigger_and_stop():
    frame = _frame([2.0] * 20 + [0.5])
    setup = analyze_narrow_range_breakout(frame, lookback=4, as_of=_after_latest_candle(frame))

    assert setup["Pattern"] == "NR4"
    assert setup["Qualifies"] is True
    assert setup["Long trigger"] == setup["Setup high"]
    assert setup["Short trigger"] == setup["Setup low"]
    assert setup["Long stop reference"] == setup["Setup low"]
    assert setup["Signal timing"] == "NEXT BAR BREAK ONLY"


def test_nr4_requires_narrowest_recent_range():
    frame = _frame([2.0] * 20 + [1.5, 1.0, 0.8, 1.2])
    setup = analyze_narrow_range_breakout(frame, lookback=4, as_of=_after_latest_candle(frame))

    assert setup["Narrowest in lookback"] is False
    assert setup["Qualifies"] is False


def test_next_bar_breakout_classification():
    setup = {
        "Qualifies": True,
        "Long trigger": 101.0,
        "Short trigger": 99.0,
    }

    assert classify_narrow_range_breakout(setup, 101.1, 99.5) == "LONG BREAKOUT"
    assert classify_narrow_range_breakout(setup, 100.5, 98.9) == "SHORT BREAKDOWN"
    assert classify_narrow_range_breakout(setup, 100.8, 99.2) == "WAITING"
    assert classify_narrow_range_breakout(setup, 101.2, 98.8) == "AMBIGUOUS — BOTH SIDES TOUCHED"


def test_rejects_invalid_or_insufficient_data():
    frame = _frame([1.0, 0.5])
    assert (
        analyze_narrow_range_breakout(
            frame,
            lookback=4,
            as_of=pd.Timestamp("2026-10-01 09:30", tz="Asia/Kolkata").to_pydatetime(),
        )
        == {}
    )
    assert classify_narrow_range_breakout({"Qualifies": False}, 10, 9) == "NO VALID SETUP"
    assert (
        classify_narrow_range_breakout(
            {"Qualifies": True, "Long trigger": 10, "Short trigger": 9}, 8, 10
        )
        == "INVALID BAR"
    )


def test_nr_setup_uses_only_completed_candles():
    frame = _frame([2.0] * 20 + [0.5])
    evaluation_time = frame.index[-1] + pd.Timedelta(minutes=1)

    setup = analyze_narrow_range_breakout(
        frame,
        lookback=4,
        as_of=evaluation_time.to_pydatetime(),
    )

    assert setup == {}


def test_nr_setup_does_not_cross_session_boundaries():
    frame = _frame([2.0] * 19 + [0.5])
    prior_session = frame.iloc[[0]].copy()
    prior_session.index = prior_session.index - pd.Timedelta(days=1)
    frame = pd.concat([prior_session, frame])

    setup = analyze_narrow_range_breakout(
        frame,
        lookback=4,
        as_of=_after_latest_candle(frame),
    )

    assert setup == {}


def test_nr_setup_rejects_gaps_in_its_completed_lookback():
    frame = _frame([2.0] * 21 + [0.5])
    frame = frame.drop(index=frame.index[-3])

    setup = analyze_narrow_range_breakout(frame, lookback=4, as_of=_after_latest_candle(frame))

    assert setup == {}
