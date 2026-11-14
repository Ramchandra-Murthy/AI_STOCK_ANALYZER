"""Tests for durable AI paper-portfolio persistence."""

from datetime import UTC, datetime

import pytest

from ai_trading.paper_trading import EquitySnapshot, PaperPortfolio
from services.ai_paper_trading_store import (
    PaperPortfolioStoreError,
    delete_portfolio,
    load_portfolio,
    save_portfolio,
)


def test_round_trip_preserves_cash_positions_trades_and_equity_history(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("AI_PAPER_TRADING_DATABASE_PATH", str(tmp_path / "paper.sqlite3"))
    portfolio = PaperPortfolio(initial_cash=10_000.0)
    portfolio.execute("RELIANCE", "BUY", 10, 100.0, signal="LONG", confidence_pct=82.5)
    portfolio.record_equity({"RELIANCE": 110.0})
    portfolio.cash = 0.0

    save_portfolio(portfolio)
    restored = load_portfolio()

    assert restored is not None
    assert restored.initial_cash == pytest.approx(10_000.0)
    assert restored.cash == pytest.approx(0.0)
    assert restored.positions == {"RELIANCE": 10}
    assert len(restored.trades) == 1
    assert restored.trades[0].signal == "LONG"
    assert restored.trades[0].confidence_pct == pytest.approx(82.5)
    assert restored.trades[0].timestamp == portfolio.trades[0].timestamp
    assert restored.equity_history == portfolio.equity_history


def test_missing_portfolio_returns_none_and_delete_is_idempotent(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AI_PAPER_TRADING_DATABASE_PATH", str(tmp_path / "paper.sqlite3"))

    assert load_portfolio() is None
    delete_portfolio()
    assert load_portfolio() is None


def test_invalid_portfolio_id_is_rejected() -> None:
    with pytest.raises(PaperPortfolioStoreError, match="portfolio_id"):
        load_portfolio(portfolio_id=" ")


def test_equity_snapshot_timestamp_round_trips(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AI_PAPER_TRADING_DATABASE_PATH", str(tmp_path / "paper.sqlite3"))
    portfolio = PaperPortfolio(initial_cash=5_000.0)
    timestamp = datetime(2026, 11, 14, 9, 30, tzinfo=UTC)
    portfolio.equity_history.append(EquitySnapshot(timestamp, 5_125.0))

    save_portfolio(portfolio)
    restored = load_portfolio()

    assert restored is not None
    assert restored.equity_history[0].timestamp == timestamp
    assert restored.equity_history[0].equity == pytest.approx(5_125.0)
