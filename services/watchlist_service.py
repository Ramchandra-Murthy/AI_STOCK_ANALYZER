"""Persistent, user-isolated storage for named stock watchlists.

Callers must pass a stable user ID from a trusted authentication provider. Never
use a user-controlled form field or a shared fallback identity as the user ID.
Set WATCHLIST_DATABASE_PATH to a durable database path in deployed environments.
"""

from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DATABASE_PATH = Path("data/watchlists.sqlite3")
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9._-]{0,31}$")


class WatchlistError(ValueError):
    """Raised when a watchlist operation receives invalid input."""


def _database_path() -> Path:
    return Path(os.environ.get("WATCHLIST_DATABASE_PATH", str(DEFAULT_DATABASE_PATH)))


def _require_user_id(user_id: str) -> str:
    if not isinstance(user_id, str) or not user_id.strip():
        raise WatchlistError("A trusted, non-empty authenticated user ID is required.")
    return user_id.strip()


def _connect() -> sqlite3.Connection:
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS watchlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, name)
        );
        CREATE TABLE IF NOT EXISTS watchlist_symbols (
            watchlist_id INTEGER NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
            symbol TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (watchlist_id, symbol)
        );
        CREATE INDEX IF NOT EXISTS idx_watchlists_user_id ON watchlists(user_id);
        """)
    return connection


def _require_name(name: str) -> str:
    normalized = name.strip() if isinstance(name, str) else ""
    if not normalized or len(normalized) > 80:
        raise WatchlistError("Watchlist name must contain 1 to 80 characters.")
    return normalized


def _require_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper() if isinstance(symbol, str) else ""
    if not SYMBOL_PATTERN.fullmatch(normalized):
        raise WatchlistError("Enter a valid stock symbol.")
    if normalized.endswith(".") or ".." in normalized:
        raise WatchlistError("Enter a valid stock symbol.")
    return normalized


def list_watchlists(user_id: str) -> list[dict[str, Any]]:
    """Return only the named watchlists owned by the given authenticated user."""
    owner = _require_user_id(user_id)
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT w.id, w.name, w.created_at, COUNT(s.symbol) AS symbol_count
            FROM watchlists AS w
            LEFT JOIN watchlist_symbols AS s ON s.watchlist_id = w.id
            WHERE w.user_id = ?
            GROUP BY w.id
            ORDER BY w.created_at, w.id
            """,
            (owner,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_watchlist(user_id: str, name: str) -> int:
    """Create a named watchlist owned by the authenticated user and return its ID."""
    owner = _require_user_id(user_id)
    normalized_name = _require_name(name)
    try:
        with _connect() as connection:
            cursor = connection.execute(
                "INSERT INTO watchlists (user_id, name) VALUES (?, ?)",
                (owner, normalized_name),
            )
            return int(cursor.lastrowid)
    except sqlite3.IntegrityError as exc:
        raise WatchlistError("A watchlist with that name already exists for this user.") from exc


def rename_watchlist(user_id: str, watchlist_id: int, name: str) -> None:
    """Rename a watchlist only when it belongs to the supplied user."""
    owner = _require_user_id(user_id)
    normalized_name = _require_name(name)
    try:
        with _connect() as connection:
            cursor = connection.execute(
                "UPDATE watchlists SET name = ? WHERE id = ? AND user_id = ?",
                (normalized_name, watchlist_id, owner),
            )
            if cursor.rowcount == 0:
                raise WatchlistError("Watchlist not found for this user.")
    except sqlite3.IntegrityError as exc:
        raise WatchlistError("A watchlist with that name already exists for this user.") from exc


def delete_watchlist(user_id: str, watchlist_id: int) -> None:
    """Delete a watchlist only when it belongs to the supplied user."""
    owner = _require_user_id(user_id)
    with _connect() as connection:
        cursor = connection.execute(
            "DELETE FROM watchlists WHERE id = ? AND user_id = ?",
            (watchlist_id, owner),
        )
        if cursor.rowcount == 0:
            raise WatchlistError("Watchlist not found for this user.")


def list_symbols(user_id: str, watchlist_id: int) -> list[str]:
    """Return symbols only when the watchlist belongs to the supplied user."""
    owner = _require_user_id(user_id)
    with _connect() as connection:
        watchlist = connection.execute(
            "SELECT id FROM watchlists WHERE id = ? AND user_id = ?",
            (watchlist_id, owner),
        ).fetchone()
        if watchlist is None:
            raise WatchlistError("Watchlist not found for this user.")
        rows = connection.execute(
            "SELECT symbol FROM watchlist_symbols WHERE watchlist_id = ? ORDER BY position, symbol",
            (watchlist_id,),
        ).fetchall()
    return [str(row["symbol"]) for row in rows]


def add_symbol(user_id: str, watchlist_id: int, symbol: str) -> bool:
    """Add a symbol; return False if it already exists in this user's watchlist."""
    owner = _require_user_id(user_id)
    normalized_symbol = _require_symbol(symbol)
    with _connect() as connection:
        watchlist = connection.execute(
            "SELECT id FROM watchlists WHERE id = ? AND user_id = ?",
            (watchlist_id, owner),
        ).fetchone()
        if watchlist is None:
            raise WatchlistError("Watchlist not found for this user.")
        existing = connection.execute(
            "SELECT 1 FROM watchlist_symbols WHERE watchlist_id = ? AND symbol = ?",
            (watchlist_id, normalized_symbol),
        ).fetchone()
        if existing:
            return False
        position = connection.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 FROM watchlist_symbols WHERE watchlist_id = ?",
            (watchlist_id,),
        ).fetchone()[0]
        connection.execute(
            "INSERT INTO watchlist_symbols (watchlist_id, symbol, position) VALUES (?, ?, ?)",
            (watchlist_id, normalized_symbol, position),
        )
    return True


def remove_symbol(user_id: str, watchlist_id: int, symbol: str) -> bool:
    """Remove a symbol only from a watchlist owned by the supplied user."""
    owner = _require_user_id(user_id)
    normalized_symbol = _require_symbol(symbol)
    with _connect() as connection:
        watchlist = connection.execute(
            "SELECT id FROM watchlists WHERE id = ? AND user_id = ?",
            (watchlist_id, owner),
        ).fetchone()
        if watchlist is None:
            raise WatchlistError("Watchlist not found for this user.")
        cursor = connection.execute(
            "DELETE FROM watchlist_symbols WHERE watchlist_id = ? AND symbol = ?",
            (watchlist_id, normalized_symbol),
        )
        return cursor.rowcount > 0
