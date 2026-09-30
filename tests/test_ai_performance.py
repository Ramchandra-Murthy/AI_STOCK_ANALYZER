"""Tests for AI paper-trading performance analytics."""

import pytest

from ai_trading.paper_trading import PaperPortfolio
from ai_trading.performance import build_performance_report


def test_performance_report_tracks_realized_and_unrealized_pnl() -> None:
    portfolio = PaperPortfolio(initial_cash=100_000.0)
    portfolio.execute("RELIANCE", "BUY", 10, 2_000.0)
    portfolio.execute("RELIANCE", "SELL", 5, 2_200.0)

    report = build_performance_report(
        portfolio.initial_cash,
        portfolio.trades,
        portfolio.positions,
        {"RELIANCE": 2_000.0},
        {"RELIANCE": 2_300.0},
        portfolio.equity({"RELIANCE": 2_300.0}),
    )

    assert report.realized_pnl == pytest.approx(1_000.0)
    assert report.unrealized_pnl == pytest.approx(1_500.0)
    assert report.total_pnl == pytest.approx(2_500.0)
    assert report.winning_trades == 1
    assert report.win_rate_pct == pytest.approx(100.0)
    assert report.trade_count == 2


def test_performance_report_calculates_drawdown_and_profit_factor() -> None:
    portfolio = PaperPortfolio(initial_cash=100_000.0)
    portfolio.execute("A", "BUY", 10, 100.0)
    portfolio.execute("A", "SELL", 10, 120.0)
    portfolio.execute("B", "BUY", 10, 100.0)
    portfolio.execute("B", "SELL", 10, 90.0)

    report = build_performance_report(
        portfolio.initial_cash,
        portfolio.trades,
        portfolio.positions,
        {},
        {},
        portfolio.equity({}),
    )

    assert report.realized_pnl == pytest.approx(100.0)
    assert report.winning_trades == 1
    assert report.losing_trades == 1
    assert report.win_rate_pct == pytest.approx(50.0)
    assert report.profit_factor == pytest.approx(2.0)
    assert report.max_drawdown_pct > 0
