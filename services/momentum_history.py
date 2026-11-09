"""Durable, bounded history for descriptive NSE/BSE momentum rankings.

Only completed scanner snapshots are stored. The module is independent of Streamlit
and market-data providers; callers decide when a snapshot is trustworthy enough to
record. SQLite is used so a scan can be written atomically without network access.
"""

from __future__ import annotations

import math
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

IST = ZoneInfo("Asia/Kolkata")
DEFAULT_DATABASE_PATH = Path("data/momentum_history.sqlite3")
HISTORY_COLUMNS = [
    "Scan time",
    "Symbol",
    "Exchange",
    "Rank",
    "Momentum strength",
    "Direction",
    "Confirmation",
    "Volume ratio",
]
CHANGE_COLUMNS = [
    "Status",
    "Rank change",
    "Score change",
    "Symbol",
    "Exchange",
    "Momentum strength",
    "Direction",
    "Confirmation",
]


class MomentumHistoryError(ValueError):
    """Raised when a momentum history snapshot is malformed."""


def _database_path(database_path: str | Path | None) -> Path:
    if database_path is not None:
        return Path(database_path)
    return Path(os.environ.get("MOMENTUM_HISTORY_DATABASE_PATH", str(DEFAULT_DATABASE_PATH)))


def _as_ist(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise MomentumHistoryError("Snapshot time must be a datetime.")
    return value.replace(tzinfo=IST) if value.tzinfo is None else value.astimezone(IST)


def _connect(database_path: str | Path | None) -> sqlite3.Connection:
    path = _database_path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS momentum_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            captured_at TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS momentum_snapshot_rows (
            snapshot_id INTEGER NOT NULL
                REFERENCES momentum_snapshots(id) ON DELETE CASCADE,
            ticker TEXT NOT NULL,
            symbol TEXT NOT NULL,
            exchange TEXT NOT NULL,
            rank INTEGER NOT NULL CHECK (rank > 0),
            score REAL NOT NULL CHECK (score >= 0 AND score <= 100),
            direction TEXT NOT NULL,
            confirmation TEXT NOT NULL,
            volume_ratio REAL,
            PRIMARY KEY (snapshot_id, ticker)
        );
        CREATE INDEX IF NOT EXISTS idx_momentum_snapshots_time
            ON momentum_snapshots(captured_at DESC);
        """
    )
    return connection


def _normalise_ranking(ranking: pd.DataFrame) -> list[tuple[object, ...]]:
    required = {
        "Symbol",
        "Exchange",
        "Rank",
        "Momentum strength",
        "Direction",
        "Confirmation",
    }
    if not isinstance(ranking, pd.DataFrame) or not required.issubset(ranking.columns):
        raise MomentumHistoryError("Ranking is missing required momentum columns.")

    rows: list[tuple[object, ...]] = []
    seen: set[tuple[str, str]] = set()
    for row in ranking.to_dict("records"):
        symbol = str(row["Symbol"]).strip().upper()
        exchange = str(row["Exchange"]).strip().upper()
        if not symbol or exchange not in {"NSE", "BSE"}:
            raise MomentumHistoryError("Each row must have a symbol and NSE/BSE exchange.")
        key = (exchange, symbol)
        if key in seen:
            raise MomentumHistoryError(f"Duplicate symbol in snapshot: {exchange}:{symbol}.")
        seen.add(key)

        try:
            rank = int(row["Rank"])
            score = float(row["Momentum strength"])
        except (TypeError, ValueError, OverflowError) as exc:
            raise MomentumHistoryError("Rank and momentum strength must be numeric.") from exc
        if rank < 1 or not math.isfinite(score) or not 0 <= score <= 100:
            raise MomentumHistoryError("Rank must be positive and score must be finite in [0, 100].")

        volume_value = row.get("Volume ratio")
        try:
            volume_ratio = None if pd.isna(volume_value) else float(volume_value)
        except (TypeError, ValueError):
            volume_ratio = None
        if volume_ratio is not None and (not math.isfinite(volume_ratio) or volume_ratio < 0):
            volume_ratio = None

        ticker = f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO"
        rows.append(
            (
                ticker,
                symbol,
                exchange,
                rank,
                score,
                str(row["Direction"]),
                str(row["Confirmation"]),
                volume_ratio,
            )
        )
    return rows


def record_momentum_snapshot(
    ranking: pd.DataFrame,
    captured_at: datetime,
    *,
    database_path: str | Path | None = None,
    max_snapshots: int = 240,
) -> int | None:
    """Atomically store one scored ranking; return its ID, or None for an empty ranking.

    A timestamp is unique, making retries idempotent. Old snapshots are pruned in the
    same transaction so storage remains bounded.
    """
    if max_snapshots < 1:
        raise MomentumHistoryError("max_snapshots must be at least one.")
    rows = _normalise_ranking(ranking)
    if not rows:
        return None
    timestamp = _as_ist(captured_at).isoformat(timespec="seconds")

    with _connect(database_path) as connection:
        connection.execute(
            "INSERT OR IGNORE INTO momentum_snapshots (captured_at) VALUES (?)", (timestamp,)
        )
        snapshot = connection.execute(
            "SELECT id FROM momentum_snapshots WHERE captured_at = ?", (timestamp,)
        ).fetchone()
        if snapshot is None:
            raise MomentumHistoryError("Could not resolve the stored momentum snapshot.")
        snapshot_id = int(snapshot["id"])
        connection.executemany(
            """
            INSERT INTO momentum_snapshot_rows (
                snapshot_id, ticker, symbol, exchange, rank, score,
                direction, confirmation, volume_ratio
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(snapshot_id, ticker) DO UPDATE SET
                rank=excluded.rank, score=excluded.score,
                direction=excluded.direction, confirmation=excluded.confirmation,
                volume_ratio=excluded.volume_ratio
            """,
            [(snapshot_id, *row) for row in rows],
        )
        connection.execute(
            """
            DELETE FROM momentum_snapshots
            WHERE id NOT IN (
                SELECT id FROM momentum_snapshots
                ORDER BY captured_at DESC, id DESC LIMIT ?
            )
            """,
            (int(max_snapshots),),
        )
    return snapshot_id


def load_momentum_history(
    *,
    database_path: str | Path | None = None,
    limit: int = 10,
) -> pd.DataFrame:
    """Load the most recent snapshots in chronological order."""
    if limit < 1:
        raise MomentumHistoryError("limit must be at least one.")
    with _connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT s.captured_at, r.symbol, r.exchange, r.rank, r.score,
                   r.direction, r.confirmation, r.volume_ratio
            FROM momentum_snapshots AS s
            JOIN momentum_snapshot_rows AS r ON r.snapshot_id = s.id
            WHERE s.id IN (
                SELECT id FROM momentum_snapshots
                ORDER BY captured_at DESC, id DESC LIMIT ?
            )
            ORDER BY s.captured_at ASC, r.rank ASC, r.ticker ASC
            """,
            (int(limit),),
        ).fetchall()
    records = [
        {
            "Scan time": row["captured_at"],
            "Symbol": row["symbol"],
            "Exchange": row["exchange"],
            "Rank": row["rank"],
            "Momentum strength": row["score"],
            "Direction": row["direction"],
            "Confirmation": row["confirmation"],
            "Volume ratio": row["volume_ratio"],
        }
        for row in rows
    ]
    return pd.DataFrame(records, columns=HISTORY_COLUMNS)


def compare_momentum_snapshots(
    current: pd.DataFrame,
    previous: pd.DataFrame | None,
) -> pd.DataFrame:
    """Compare two full rankings; positive rank change means a stock moved up."""
    if current is None or current.empty:
        return pd.DataFrame(columns=CHANGE_COLUMNS)
    previous = previous if isinstance(previous, pd.DataFrame) else pd.DataFrame()
    required = {"Symbol", "Exchange", "Rank", "Momentum strength", "Direction"}
    if not required.issubset(current.columns):
        raise MomentumHistoryError("Current ranking is missing comparison columns.")
    previous_by_key: dict[tuple[str, str], dict[str, object]] = {}
    if required.issubset(previous.columns):
        previous_by_key = {
            (str(row["Exchange"]), str(row["Symbol"])): row
            for row in previous.to_dict("records")
        }

    current_keys: set[tuple[str, str]] = set()
    rows: list[dict[str, object]] = []
    for row in current.to_dict("records"):
        key = (str(row["Exchange"]), str(row["Symbol"]))
        current_keys.add(key)
        old = previous_by_key.get(key)
        if old is None:
            rank_change = None
            score_change = None
            status = "NEW"
        else:
            rank_change = int(old["Rank"]) - int(row["Rank"])
            score_change = round(
                float(row["Momentum strength"]) - float(old["Momentum strength"]), 2
            )
            if rank_change > 0:
                status = "RANK UP"
            elif rank_change < 0:
                status = "RANK DOWN"
            elif score_change > 0:
                status = "STRENGTHENING"
            elif score_change < 0:
                status = "WEAKENING"
            else:
                status = "STABLE"
        rows.append(
            {
                "Status": status,
                "Rank change": rank_change,
                "Score change": score_change,
                "Symbol": row["Symbol"],
                "Exchange": row["Exchange"],
                "Momentum strength": row["Momentum strength"],
                "Direction": row["Direction"],
                "Confirmation": row.get("Confirmation", "NONE"),
            }
        )

    for key, old in previous_by_key.items():
        if key not in current_keys:
            rows.append(
                {
                    "Status": "DROPPED",
                    "Rank change": None,
                    "Score change": None,
                    "Symbol": key[1],
                    "Exchange": key[0],
                    "Momentum strength": None,
                    "Direction": old.get("Direction"),
                    "Confirmation": old.get("Confirmation", "NONE"),
                }
            )
    order = {
        "RANK UP": 0,
        "STRENGTHENING": 1,
        "NEW": 2,
        "STABLE": 3,
        "WEAKENING": 4,
        "RANK DOWN": 5,
        "DROPPED": 6,
    }
    result = pd.DataFrame(rows, columns=CHANGE_COLUMNS)
    result["_order"] = result["Status"].map(order).fillna(len(order))
    return (
        result.sort_values(["_order", "Rank change"], ascending=[True, False], na_position="last")
        .drop(columns="_order")
        .reset_index(drop=True)
    )
