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
