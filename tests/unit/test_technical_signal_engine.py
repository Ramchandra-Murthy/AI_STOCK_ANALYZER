import pandas as pd
import pytest

from engine.signal_engine import _recommendation_for_score, generate_signal


@pytest.mark.parametrize(
    ("score", "recommendation"),
    [
        (0, "STRONG SELL"),
        (15, "STRONG SELL"),
        (50, "HOLD"),
        (70, "BUY"),
        (85, "STRONG BUY"),
        (100, "STRONG BUY"),
    ],
)
def test_recommendation_thresholds_are_unchanged(score: int, recommendation: str) -> None:
    assert _recommendation_for_score(score) == recommendation


def test_technical_score_is_not_reported_as_predictive_confidence() -> None:
    frame = pd.DataFrame(
        [
            {
                "SMA_20": 110.0,
                "SMA_50": 100.0,
                "EMA_20": 115.0,
                "RSI_14": 50.0,
                "MACD": 2.0,
                "Signal": 1.0,
                "Close": 112.0,
            }
        ]
    )

    result = generate_signal(frame)

    assert result["Status"] == "OK"
    assert result["Score"] == 85
    assert result["Recommendation"] == "STRONG BUY"
    assert result["Confidence"] is None
    assert result["Confidence Status"] == "Not calibrated"
