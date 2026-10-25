import math

import pandas as pd
import pytest

from engine.signal_engine import generate_signal


def _baseline_frame(**overrides: float) -> pd.DataFrame:
    values = {
        "SMA_20": 100.0,
        "SMA_50": 100.0,
        "EMA_20": 100.0,
        "RSI_14": 50.0,
        "MACD": 1.0,
        "Signal": 1.0,
        "Close": 100.0,
    }
    values.update(overrides)
    return pd.DataFrame([values])


@pytest.mark.parametrize(
    ("optional_values", "expected_score", "expected_reason"),
    [
        ({"BB_Lower": 101.0}, 25, "Price below Lower Bollinger Band"),
        ({"BB_Upper": 99.0}, 5, "Price above Upper Bollinger Band"),
        ({"Support": 102.0}, 25, "Trading near Support"),
        ({"Resistance": 99.0}, 5, "Trading near Resistance"),
        ({"ATR": 6.0}, 10, "High Volatility"),
        ({"ATR": 1.0}, 20, "Low Volatility"),
    ],
)
def test_optional_indicator_adjustments_have_matching_reasons(
    optional_values: dict[str, float], expected_score: int, expected_reason: str
) -> None:
    result = generate_signal(_baseline_frame(**optional_values))

    assert result["Status"] == "OK"
    assert result["Score"] == expected_score
    assert expected_reason in result["Reasons"]


def test_optional_indicators_may_be_absent_without_changing_base_signal() -> None:
    result = generate_signal(_baseline_frame())

    assert result["Status"] == "OK"
    assert result["Score"] == 15
    assert result["Reasons"] == [
        "20 SMA below 50 SMA (Bearish)",
        "EMA20 below SMA20",
        "RSI Neutral",
        "MACD Bearish Crossover",
    ]


@pytest.mark.parametrize("invalid_value", [float("nan"), float("inf"), -float("inf")])
def test_invalid_optional_indicator_values_are_ignored(invalid_value: float) -> None:
    frame = _baseline_frame(BB_Lower=invalid_value, BB_Upper=invalid_value,
                            Support=invalid_value, Resistance=invalid_value,
                            ATR=invalid_value)

    result = generate_signal(frame)

    assert result["Status"] == "OK"
    assert result["Score"] == 15
    assert not any(
        reason in result["Reasons"]
        for reason in (
            "Price below Lower Bollinger Band",
            "Price above Upper Bollinger Band",
            "Trading near Support",
            "Trading near Resistance",
            "High Volatility",
            "Low Volatility",
        )
    )


@pytest.mark.parametrize(
    ("overrides", "expected_score", "expected_reason"),
    [
        ({"Close": 100.0, "BB_Lower": 100.0}, 15, None),
        ({"Close": 100.0, "BB_Upper": 100.0}, 15, None),
        ({"Close": 100.0, "ATR": 2.0}, 15, None),
    ],
)
def test_optional_indicator_threshold_equality_does_not_trigger_adjustment(
    overrides: dict[str, float], expected_score: int, expected_reason: str | None
) -> None:
    result = generate_signal(_baseline_frame(**overrides))

    assert result["Status"] == "OK"
    assert result["Score"] == expected_score
    if expected_reason is not None:
        assert expected_reason in result["Reasons"]
