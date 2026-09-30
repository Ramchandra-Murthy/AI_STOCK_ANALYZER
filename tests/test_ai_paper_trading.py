"""Tests for the AI paper-trading portfolio engine."""

import pandas as pd
import pytest

from ai_trading.paper_trading import PaperPortfolio, apply_ml_signals


def test_apply_long_signal_buys_and_marks_equity() -> None:
    portfolio = PaperPortfolio(initial_cash=100_000.0)
    signals = pd.DataFrame(
        [{"symbol": "RELIANCE", "signal": "LONG", "confidence_pct": 80.0}]
    )

    trades = apply_ml_signals(
        portfolio,
        signals,
        {"RELIANCE": 2_000.0},
        capital_fraction=0.20,
        max_positions=5,
    )

    assert len(trades) == 1
    assert trades[0].side == "BUY"
    assert portfolio.positions["RELIANCE"] == 10
    assert portfolio.equity({"RELIANCE": 2_100.0}) == pytest.approx(101_000.0)


def test_non_long_signal_closes_existing_position() -> None:
    portfolio = PaperPortfolio(initial_cash=100_000.0)
    portfolio.execute("TCS", "BUY", 10, 4_000.0)
    signals = pd.DataFrame([{"symbol": "TCS", "signal": "SHORT"}])

    trades = apply_ml_signals(portfolio, signals, {"TCS": 3_900.0})

    assert len(trades) == 1
    assert trades[0].side == "SELL"
    assert "TCS" not in portfolio.positions
    assert portfolio.cash == pytest.approx(99_000.0)


def test_position_limit_is_respected() -> None:
    portfolio = PaperPortfolio(initial_cash=100_000.0)
    signals = pd.DataFrame(
        [
            {"symbol": "A", "signal": "LONG", "confidence_pct": 90.0},
            {"symbol": "B", "signal": "LONG", "confidence_pct": 80.0},
            {"symbol": "C", "signal": "LONG", "confidence_pct": 70.0},
        ]
    )

    apply_ml_signals(
        portfolio,
        signals,
        {"A": 100.0, "B": 100.0, "C": 100.0},
        capital_fraction=0.90,
        max_positions=2,
    )

    assert set(portfolio.positions) == {"A", "B"}
