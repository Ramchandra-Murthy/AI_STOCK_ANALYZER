"""SQLite persistence for validated trading profiles.

The local store is deliberately independent of Supabase and broker credentials.
Set TRADING_PROFILES_DATABASE_PATH to a durable writable path in deployments.
"""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Any

from algorithmic_trading.trading_profile import TradingProfile

DEFAULT_DATABASE_PATH = Path("data/trading_profiles.sqlite3")


class TradingProfileStoreError(ValueError):
    """Raised for invalid or unavailable trading-profile operations."""


def _database_path() -> Path:
    return Path(os.environ.get("TRADING_PROFILES_DATABASE_PATH", str(DEFAULT_DATABASE_PATH)))


def _connect() -> sqlite3.Connection:
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS trading_profiles (
            name TEXT PRIMARY KEY COLLATE NOCASE,
            profile_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return connection


def _validated_profile(profile: TradingProfile) -> TradingProfile:
    if not isinstance(profile, TradingProfile):
        raise TradingProfileStoreError("A validated TradingProfile is required.")
    return profile


def save_profile(profile: TradingProfile) -> None:
    """Insert or replace a profile by its case-insensitive name."""
    profile = _validated_profile(profile)
    payload = json.dumps(asdict(profile), sort_keys=True, allow_nan=False)
    try:
        with _connect() as connection:
            connection.execute(
                """
                INSERT INTO trading_profiles (name, profile_json)
                VALUES (?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    profile_json = excluded.profile_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (profile.name.strip(), payload),
            )
    except (sqlite3.Error, TypeError, ValueError) as exc:
        raise TradingProfileStoreError(f"Could not save trading profile: {exc}") from exc


def list_profiles() -> list[str]:
    """Return saved profile names in stable alphabetical order."""
    try:
        with _connect() as connection:
            rows = connection.execute(
                "SELECT name FROM trading_profiles ORDER BY name COLLATE NOCASE"
            ).fetchall()
        return [str(row["name"]) for row in rows]
    except sqlite3.Error as exc:
        raise TradingProfileStoreError(f"Could not list trading profiles: {exc}") from exc


def load_profile(name: str) -> TradingProfile:
    """Load and revalidate a saved profile."""
    normalized = name.strip() if isinstance(name, str) else ""
    if not normalized:
        raise TradingProfileStoreError("Profile name is required.")
    try:
        with _connect() as connection:
            row = connection.execute(
                "SELECT profile_json FROM trading_profiles WHERE name = ?",
                (normalized,),
            ).fetchone()
        if row is None:
            raise TradingProfileStoreError(f"Trading profile '{normalized}' was not found.")
        values: dict[str, Any] = json.loads(row["profile_json"])
        return TradingProfile(**values)
    except TradingProfileStoreError:
        raise
    except (sqlite3.Error, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise TradingProfileStoreError(f"Could not load trading profile: {exc}") from exc


def delete_profile(name: str) -> None:
    """Delete one saved profile; never silently ignore an unknown name."""
    normalized = name.strip() if isinstance(name, str) else ""
    if not normalized:
        raise TradingProfileStoreError("Profile name is required.")
    try:
        with _connect() as connection:
            cursor = connection.execute(
                "DELETE FROM trading_profiles WHERE name = ?", (normalized,)
            )
            if cursor.rowcount == 0:
                raise TradingProfileStoreError(f"Trading profile '{normalized}' was not found.")
    except TradingProfileStoreError:
        raise
    except sqlite3.Error as exc:
        raise TradingProfileStoreError(f"Could not delete trading profile: {exc}") from exc
