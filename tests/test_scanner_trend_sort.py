import pandas as pd

from services.scanner_trend_sort import sort_bullish_to_bearish


def test_sort_orders_trend_groups_bullish_to_bearish_and_strength_within_group() -> None:
    frame = pd.DataFrame(
        {
            "Symbol": ["BEAR", "BULL_LOW", "UNKNOWN", "SIDE", "BULL_HIGH", "STRONG_BEAR"],
            "Trend": ["Bearish", "Bullish", "Unknown", "Sideways", "Bullish", "Strong Bearish"],
            "AI Score": [80, 35, 99, 50, 70, 100],
        }
    )

    result = sort_bullish_to_bearish(frame)

    assert result["Symbol"].tolist() == [
        "BULL_HIGH",
        "BULL_LOW",
        "SIDE",
        "UNKNOWN",
        "BEAR",
        "STRONG_BEAR",
    ]
    assert "__trend_order_rank__" not in result.columns


def test_sort_uses_regime_before_signal_and_keeps_unknown_last() -> None:
    frame = pd.DataFrame(
        {
            "symbol": ["bearish_regime", "bullish_regime", "unknown"],
            "regime": ["BEARISH", "BULLISH", "INSUFFICIENT DATA"],
            "signal": ["LONG", "SHORT", "LONG"],
            "confidence_pct": [90, 95, 99],
        }
    )

    result = sort_bullish_to_bearish(frame)

    assert result["symbol"].tolist() == ["bullish_regime", "unknown", "bearish_regime"]


def test_sort_returns_copy_without_reordering_when_no_trend_column_exists() -> None:
    frame = pd.DataFrame({"Symbol": ["A", "B"], "Change %": [-1.0, 2.0]})

    result = sort_bullish_to_bearish(frame)

    assert result["Symbol"].tolist() == ["A", "B"]
    assert result is not frame
