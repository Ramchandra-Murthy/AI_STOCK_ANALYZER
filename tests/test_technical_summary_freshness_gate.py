from unittest.mock import MagicMock, patch

import pandas as pd

from components.technical_summary import show_technical_summary


def _history():
    return pd.DataFrame(
        [
            {
                "Close": 110.0,
                "EMA20": 108.0,
                "EMA50": 105.0,
                "EMA200": 100.0,
                "RSI": 60.0,
                "MACD": 2.0,
                "MACD_Signal": 1.0,
                "ATR": 3.0,
                "Support": 102.0,
                "Resistance": 115.0,
                "Volume": 1200.0,
                "Volume_MA20": 1000.0,
            }
        ]
    )


def test_withholds_buy_hold_sell_when_freshness_is_unverified():
    fake_streamlit = MagicMock()
    fake_streamlit.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]

    with patch("components.technical_summary.st", fake_streamlit):
        show_technical_summary(
            _history(),
            allow_recommendation=False,
            block_reason="Data status: STALE; latest candle: 2026-10-10.",
        )

    fake_streamlit.warning.assert_called_once()
    warning = fake_streamlit.warning.call_args.args[0]
    assert "Recommendation withheld" in warning
    assert "Data status: STALE" in warning
    fake_streamlit.success.assert_not_called()


def test_shows_recommendation_when_freshness_gate_allows_it():
    fake_streamlit = MagicMock()
    fake_streamlit.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]

    with patch("components.technical_summary.st", fake_streamlit):
        show_technical_summary(_history(), allow_recommendation=True)

    fake_streamlit.success.assert_called_once()
    assert "Recommendation" in fake_streamlit.success.call_args.args[0]
    fake_streamlit.warning.assert_not_called()


def test_missing_required_column_withholds_summary():
    fake_streamlit = MagicMock()
    history = _history().drop(columns=["MACD_Signal"])

    with patch("components.technical_summary.st", fake_streamlit):
        show_technical_summary(history)

    fake_streamlit.warning.assert_called_once()
    assert "missing required indicator" in fake_streamlit.warning.call_args.args[0].lower()
    fake_streamlit.success.assert_not_called()


def test_non_finite_latest_indicator_withholds_recommendation():
    fake_streamlit = MagicMock()
    history = _history()
    history.loc[history.index[-1], "RSI"] = float("nan")

    with patch("components.technical_summary.st", fake_streamlit):
        show_technical_summary(history)

    fake_streamlit.warning.assert_called_once()
    assert "RSI" in fake_streamlit.warning.call_args.args[0]
    fake_streamlit.success.assert_not_called()


def test_invalid_rsi_withholds_recommendation():
    fake_streamlit = MagicMock()
    history = _history()
    history.loc[history.index[-1], "RSI"] = 150.0

    with patch("components.technical_summary.st", fake_streamlit):
        show_technical_summary(history)

    fake_streamlit.warning.assert_called_once()
    assert "RSI must be between 0 and 100" in fake_streamlit.warning.call_args.args[0]
    fake_streamlit.success.assert_not_called()


def test_mixed_ema_structure_is_not_labelled_sideways():
    fake_streamlit = MagicMock()
    history = _history()
    history.loc[history.index[-1], "EMA20"] = 109.0
    history.loc[history.index[-1], "EMA50"] = 105.0
    history.loc[history.index[-1], "EMA200"] = 100.0
    history.loc[history.index[-1], "Close"] = 108.0

    with patch("components.technical_summary.st", fake_streamlit):
        show_technical_summary(history)

    trend_metric = fake_streamlit.columns.return_value[0].metric
    assert trend_metric.call_args.args[0] == "Trend"
    assert trend_metric.call_args.args[1] == "🟢 Bullish Structure"


def test_missing_volume_is_reported_as_unavailable():
    fake_streamlit = MagicMock()
    history = _history().drop(columns=["Volume_MA20"])

    with patch("components.technical_summary.st", fake_streamlit):
        show_technical_summary(history)

    assert fake_streamlit.metric.call_args.args == ("Volume", "Unavailable")
