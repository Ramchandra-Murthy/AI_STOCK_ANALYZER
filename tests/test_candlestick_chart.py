import pandas as pd
import pytest

from components.charts.candlestick_chart import plot_candlestick


def _history(index):
    return pd.DataFrame(
        {
            "Open": [100.0] * len(index),
            "High": [105.0] * len(index),
            "Low": [95.0] * len(index),
            "Close": [102.0] * len(index),
            "Volume": [1000] * len(index),
            "EMA20": [101.0] * len(index),
        },
        index=index,
    )


def test_chart_sorts_dates_and_removes_duplicate_dates():
    dates = ["2026-10-15", "2026-10-13", "2026-10-13", "2026-10-14"]
    chart = plot_candlestick(_history(dates))

    candle = next(trace for trace in chart.data if trace.type == "candlestick")
    candle_dates = pd.to_datetime(candle.x, utc=True)

    assert list(candle_dates) == sorted(candle_dates)
    assert len(candle_dates) == 3
    assert len(set(candle_dates)) == 3


def test_chart_drops_invalid_dates_and_aligns_volume_axis():
    chart = plot_candlestick(_history(["2026-10-14", "not-a-date", "2026-10-16"]))

    candle = next(trace for trace in chart.data if trace.type == "candlestick")
    volume = next(trace for trace in chart.data if trace.type == "bar")

    assert len(candle.x) == 2
    assert list(candle.x) == list(volume.x)
    assert chart.layout.xaxis.range == chart.layout.xaxis2.range


def test_chart_rejects_history_with_no_valid_dates():
    with pytest.raises(ValueError, match="No valid dated price rows"):
        plot_candlestick(_history(["not-a-date", "also-not-a-date"]))
