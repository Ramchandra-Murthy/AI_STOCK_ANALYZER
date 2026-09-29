import pandas as pd
import pytest

from engine.regime_engine import (
    composite_regime_score,
    regime_breakout,
    regime_ema,
    regime_sma,
    turtle_trader,
)


def test_breakout_sets_and_carries_regime() -> None:
    frame = pd.DataFrame({"High": [10, 11, 12, 11, 10], "Low": [9, 8, 7, 8, 6]})
    result = regime_breakout(frame, periods=3)

    assert result.iloc[2] == 1
    assert result.iloc[3] == 1
    assert result.iloc[4] == -1


def test_sma_regime_uses_short_minus_long() -> None:
    frame = pd.DataFrame({"Close": [1, 2, 3, 4, 5, 4, 3]})
    result = regime_sma(frame, short_period=2, long_period=4)

    assert pd.isna(result.iloc[2])
    assert result.iloc[3] == 1
    assert result.iloc[-1] == -1


def test_ema_regime_uses_short_minus_long() -> None:
    frame = pd.DataFrame({"Close": [1, 2, 3, 4, 5, 4, 3]})
    result = regime_ema(frame, short_period=2, long_period=4)

    assert result.iloc[3] == 1
    assert result.iloc[-1] == -1


def test_turtle_returns_only_directional_or_neutral_states() -> None:
    frame = pd.DataFrame({"High": [10, 11, 12, 11, 10, 9], "Low": [9, 8, 7, 8, 9, 6]})
    result = turtle_trader(frame, entry_period=4, exit_period=2)

    assert set(result.unique()).issubset({-1, 0, 1})


def test_composite_regime_score_aligns_signals() -> None:
    first = pd.Series([1, 1, -1], name="a")
    second = pd.Series([1, -1, -1], name="b")

    result = composite_regime_score(first, second)

    assert result.tolist() == [2, 0, -2]


def test_breakout_rejects_invalid_period() -> None:
    frame = pd.DataFrame({"High": [1, 2], "Low": [0, 1]})

    with pytest.raises(ValueError):
        regime_breakout(frame, periods=1)
