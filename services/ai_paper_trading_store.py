"""Durable SQLite storage for the AI paper-trading portfolio.

This store contains simulated trades only. It has no broker or order-routing
integration. Configure AI_PAPER_TRADING_DATABASE_PATH for a durable writable
location in deployed environments.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_trading.paper_trading import EquitySnapshot, PaperPortfolio, PaperTrade

DEFAULT_DATABASE_PATH = Path("data/ai_paper_trading.sqlite3")


class PaperPortfolioStoreError(ValueError):
    """Raised when a paper portfolio cannot be saved or restored."""


def _database_path() -> Path:
    return Path(os.environ.get("AI_PAPER_TRADING_DATABASE_PATH", str(DEFAULT_DATABASE_PATH)))


def _connect() -> sqlite3.Connection:
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.execute("""
        CREATE TABLE IF NOT EXISTS ai_paper_portfolios (
            portfolio_id TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)
    return connection


def _portfolio_payload(portfolio: PaperPortfolio) -> str:
    if not isinstance(portfolio, PaperPortfolio):
        raise PaperPortfolioStoreError("A valid AI paper portfolio is required.")
    payload: dict[str, Any] = {
        "initial_cash": portfolio.initial_cash,
        "cash": portfolio.cash,
        "positions": portfolio.positions,
        "trades": [
            {
                "symbol": trade.symbol,
                "side": trade.side,
                "quantity": trade.quantity,
                "price": trade.price,
                "value": trade.value,
                "cash_after": trade.cash_after,
                "signal": trade.signal,
                "confidence_pct": trade.confidence_pct,
                "reason": trade.reason,
                "timestamp": trade.timestamp.isoformat(),
            }
            for trade in portfolio.trades
        ],
        "equity_history": [
            {"timestamp": item.timestamp.isoformat(), "equity": item.equity}
            for item in portfolio.equity_history
        ],
    }
    try:
        return json.dumps(payload, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise PaperPortfolioStoreError(f"Could not serialize paper portfolio: {exc}") from exc


def save_portfolio(portfolio: PaperPortfolio, *, portfolio_id: str = "default") -> None:
    """Atomically save the current simulated portfolio state."""
    if not portfolio_id.strip():
        raise PaperPortfolioStoreError("portfolio_id must not be empty.")
    payload = _portfolio_payload(portfolio)
    try:
        with _connect() as connection:
            connection.execute(
                """
                INSERT INTO ai_paper_portfolios (portfolio_id, payload_json)
                VALUES (?, ?)
                ON CONFLICT(portfolio_id) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (portfolio_id, payload),
            )
    except (sqlite3.Error, OSError) as exc:
        raise PaperPortfolioStoreError(f"Could not save paper portfolio: {exc}") from exc


def load_portfolio(*, portfolio_id: str = "default") -> PaperPortfolio | None:
    """Restore a saved portfolio, or return None when no session exists."""
    if not portfolio_id.strip():
        raise PaperPortfolioStoreError("portfolio_id must not be empty.")
    try:
        with _connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM ai_paper_portfolios WHERE portfolio_id = ?",
                (portfolio_id,),
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(row["payload_json"])
        portfolio = PaperPortfolio(initial_cash=float(payload["initial_cash"]))
        # Assign after construction so a fully invested portfolio with zero cash
        # is restored exactly rather than interpreted as an uninitialized balance.
        portfolio.cash = float(payload["cash"])
        portfolio.positions = {
            str(symbol): int(quantity) for symbol, quantity in payload["positions"].items()
        }
        portfolio.trades = [
            PaperTrade(
                symbol=str(item["symbol"]),
                side=str(item["side"]),
                quantity=int(item["quantity"]),
                price=float(item["price"]),
                value=float(item["value"]),
                cash_after=float(item["cash_after"]),
                signal=item.get("signal"),
                confidence_pct=item.get("confidence_pct"),
                reason=str(item.get("reason", "manual")),
                timestamp=datetime.fromisoformat(item["timestamp"]),
            )
            for item in payload["trades"]
        ]
        portfolio.equity_history = [
            EquitySnapshot(
                timestamp=datetime.fromisoformat(item["timestamp"]),
                equity=float(item["equity"]),
            )
            for item in payload["equity_history"]
        ]
        if portfolio.cash < 0 or portfolio.initial_cash <= 0:
            raise ValueError("saved cash or initial capital is invalid")
        return portfolio
    except (sqlite3.Error, OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, PaperPortfolioStoreError):
            raise
        raise PaperPortfolioStoreError(f"Could not load paper portfolio: {exc}") from exc


def delete_portfolio(*, portfolio_id: str = "default") -> None:
    """Delete one saved paper session; a missing session is harmless."""
    if not portfolio_id.strip():
        raise PaperPortfolioStoreError("portfolio_id must not be empty.")
    try:
        with _connect() as connection:
            connection.execute(
                "DELETE FROM ai_paper_portfolios WHERE portfolio_id = ?", (portfolio_id,)
            )
    except (sqlite3.Error, OSError) as exc:
        raise PaperPortfolioStoreError(f"Could not delete paper portfolio: {exc}") from exc
