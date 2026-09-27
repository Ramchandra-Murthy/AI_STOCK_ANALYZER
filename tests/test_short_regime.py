import pandas as pd
import pytest

from scanner.short_regime import regime_breakdown


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
