import pandas as pd
import pytest

from engine.signal_engine import _recommendation_for_score, generate_signal


@pytest.mark.parametrize(
    ("score", "recommendation"),
    [
        (0, "STRONG SELL"),
        (15, "STRONG SELL"),
        (24, "STRONG SELL"),
        (25, "SELL"),
        (44, "SELL"),
        (45, "HOLD"),
        (69, "HOLD"),
        (70, "BUY"),
        (84, "BUY"),
        (85, "STRONG BUY"),
        (100, "STRONG BUY"),
    ],
)
def test_recommendation_thresholds_are_unchanged(score: int, recommendation: str) -> None:
    assert _recommendation_for_score(score) == recommendation


def _signal_frame(**overrides: float) -> pd.DataFrame:
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


def test_technical_score_is_not_reported_as_predictive_confidence() -> None:
    result = generate_signal(
        _signal_frame(SMA_20=110.0, SMA_50=100.0, EMA_20=115.0, RSI_14=65.0, MACD=2.0, Signal=1.0, Close=112.0)
    )

    assert result["Status"] == "OK"
    assert result["Score"] == 85
    assert result["Recommendation"] == "STRONG BUY"
    assert result["Confidence"] is None
    assert result["Confidence Status"] == "Not calibrated"


def test_zero_score_never_becomes_one_hundred_percent_confidence() -> None:
    result = generate_signal(
        _signal_frame(
            SMA_20=90.0,
            SMA_50=100.0,
            EMA_20=80.0,
            RSI_14=75.0,
            MACD=0.0,
            Signal=1.0,
            Close=120.0,
            BB_Upper=110.0,
            Resistance=120.0,
            ATR=10.0,
        )
    )

    assert result["Status"] == "OK"
    assert result["Score"] == 0
    assert result["Confidence"] is None
    assert result["Confidence Status"] == "Not calibrated"


@pytest.mark.parametrize(
    ("rsi", "expected_adjustment", "expected_reason"),
    [
        (29.99, 20, "RSI Oversold"),
        (30.0, 10, "RSI Bullish Zone"),
        (45.0, 10, "RSI Bullish Zone"),
        (45.01, 5, "RSI Neutral"),
        (59.99, 5, "RSI Neutral"),
        (60.0, -5, "RSI Slightly Overbought"),
        (69.99, -5, "RSI Slightly Overbought"),
        (70.0, -20, "RSI Overbought"),
    ],
)
def test_rsi_boundaries_apply_expected_score_adjustment(
    rsi: float, expected_adjustment: int, expected_reason: str
) -> None:
    result = generate_signal(_signal_frame(RSI_14=rsi))

    assert result["Status"] == "OK"
    assert result["Score"] == 50 + expected_adjustment
    assert expected_reason in result["Reasons"]


@pytest.mark.parametrize(
    ("macd", "signal_line", "expected_score", "expected_reason"),
    [
        (1.01, 1.0, 65, "MACD Bullish Crossover"),
        (1.0, 1.0, 35, "MACD Bearish Crossover"),
        (0.99, 1.0, 35, "MACD Bearish Crossover"),
    ],
)
def test_macd_crossover_uses_macd_relative_to_signal_line(
    macd: float, signal_line: float, expected_score: int, expected_reason: str
) -> None:
    result = generate_signal(_signal_frame(MACD=macd, Signal=signal_line))

    assert result["Status"] == "OK"
    assert result["Score"] == expected_score
    assert expected_reason in result["Reasons"]


def test_score_adjustments_and_reasons_match_for_support_resistance_and_volatility() -> None:
    result = generate_signal(
        _signal_frame(
            SMA_20=110.0,
            SMA_50=100.0,
            EMA_20=100.0,
            RSI_14=50.0,
            MACD=2.0,
            Signal=1.0,
            Close=100.0,
            Support=102.0,
            Resistance=99.0,
            ATR=6.0,
        )
    )

    # Base 50 + SMA 15 - EMA 10 + neutral RSI 5 + MACD 15
    # + support 10 - resistance 10 - high-volatility penalty 5 = 70.
    assert result["Status"] == "OK"
    assert result["Score"] == 70
    assert result["Risk"] == "High"
    assert "Trading near Support" in result["Reasons"]
    assert "Trading near Resistance" in result["Reasons"]
    assert "High Volatility" in result["Reasons"]


@pytest.mark.parametrize(
    ("score", "recommendation"),
    [
        (69, "HOLD"),
        (70, "BUY"),
        (84, "BUY"),
        (85, "STRONG BUY"),
    ],
)
def test_score_recommendation_boundaries(score: int, recommendation: str) -> None:
    assert _recommendation_for_score(score) == recommendation
