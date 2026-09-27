import pandas as pd
import pytest

from scanner.short_regime import (
    moving_average_regime,
    regime_breakdown,
    turtle_regime,

    moving_average_regime,
    regime_breakdown,
    turtle_regime,
)


def test_fresh_high_is_bullish_after_lookback():
    frame = pd.DataFrame(
        {
            "High": [10, 11, 12, 13, 15],
            "Low": [8, 9, 10, 11, 12],
        }
    )

    result = regime_breakdown(frame, high_lookback=3, low_lookback=3)

    assert result.iloc[3] == "BULLISH"
    assert result.iloc[4] == "BULLISH"


def test_fresh_low_is_bearish_after_lookback():
    frame = pd.DataFrame(
        {
            "High": [15, 14, 13, 12, 11],
            "Low": [10, 9, 8, 7, 5],
        }
    )

    result = regime_breakdown(frame, high_lookback=3, low_lookback=3)

    assert result.iloc[3] == "BEARISH"
    assert result.iloc[4] == "BEARISH"


def test_current_bar_is_not_used_as_its_own_breakout_reference():
    frame = pd.DataFrame(
        {
            "High": [10, 11, 12, 12],
            "Low": [8, 9, 10, 10],
        }
    )

    result = regime_breakdown(frame, high_lookback=3, low_lookback=3)

    assert result.iloc[3] == "NEUTRAL"


def test_invalid_lookback_and_missing_columns_are_rejected():
    with pytest.raises(ValueError):
        regime_breakdown(pd.DataFrame({"High": [1], "Low": [1]}), high_lookback=0)

    with pytest.raises(ValueError):
        regime_breakdown(pd.DataFrame({"Close": [1]}), low_lookback=3)


def test_turtle_regime_requires_long_and_short_breakouts_to_agree():
    frame = pd.DataFrame(
        {
            "High": [15, 14, 13, 12, 11, 10],
            "Low": [10, 9, 8, 7, 6, 5],
        }
    )

    result = turtle_regime(frame, entry_lookback=4, exit_lookback=2)

    assert result.iloc[:4].tolist() == ["NEUTRAL"] * 4
    assert result.iloc[4] == "BEARISH"
    assert result.iloc[5] == "BEARISH"


def test_turtle_regime_stays_neutral_when_fast_regime_disagrees():
    frame = pd.DataFrame(
        {
            "High": [10, 11, 12, 13, 12],
            "Low": [8, 9, 10, 11, 10],
        }
    )

    result = turtle_regime(frame, entry_lookback=3, exit_lookback=2)

    assert result.iloc[3] == "BULLISH"
    assert result.iloc[4] == "NEUTRAL"


def test_turtle_regime_rejects_invalid_lookbacks():
    frame = pd.DataFrame({"High": [10, 11], "Low": [8, 9]})

    with pytest.raises(ValueError):
        turtle_regime(frame, entry_lookback=0)


def test_moving_average_regime_classifies_fast_above_and_below_slow():
    frame = pd.DataFrame({"Close": [1, 2, 3, 4, 3, 2]})
    result = moving_average_regime(frame, fast_window=2, slow_window=3)
    assert result.iloc[:2].tolist() == ["NEUTRAL", "NEUTRAL"]
    assert result.iloc[2] == "BULLISH"
    assert result.iloc[5] == "BEARISH"


def test_moving_average_regime_does_not_use_current_bar_in_its_window():
    frame = pd.DataFrame({"Close": [10, 10, 10, 20]})
    result = moving_average_regime(frame, fast_window=2, slow_window=3)
    assert result.iloc[2] == "NEUTRAL"
    assert result.iloc[3] == "BULLISH"


def test_moving_average_regime_rejects_invalid_windows_and_missing_price():
    frame = pd.DataFrame({"Close": [1, 2, 3]})
    with pytest.raises(ValueError):
        moving_average_regime(frame, fast_window=3, slow_window=3)
    with pytest.raises(ValueError):
        moving_average_regime(frame, fast_window=4, slow_window=3)
    with pytest.raises(ValueError):
        moving_average_regime(pd.DataFrame({"Open": [1, 2]}))
