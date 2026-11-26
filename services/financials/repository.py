from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from core.exceptions import RepositoryError
from services.financials.balance_sheet import BalanceSheet
from services.financials.cash_flow import CashFlowStatement
from services.financials.financial_statement import (
    FinancialStatements,
    PeriodFinancials,
)
from services.financials.income_statement import IncomeStatement


SCHEMA_VERSION = 1
DEFAULT_DB_PATH = Path("data/financial_statements.sqlite3")


class FinancialStatementRepository:
    """SQLite-backed, append-only repository for financial statement snapshots.

    Each successful save creates a new version. Existing versions are never
    overwritten by the repository API. The database path can be overridden
    with AI_STOCK_FINANCIALS_DB or supplied explicitly for isolated tests.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        configured_path = db_path or os.getenv(
            "AI_STOCK_FINANCIALS_DB", str(DEFAULT_DB_PATH)
        )
        self.db_path = Path(configured_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS financial_statement_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    company_name_key TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    fiscal_year TEXT NOT NULL,
                    period_end TEXT,
                    period_type TEXT NOT NULL DEFAULT 'FY',
                    currency TEXT NOT NULL,
                    version INTEGER NOT NULL CHECK (version >= 1),
                    source_provider TEXT,
                    source_type TEXT,
                    source_reference TEXT,
                    retrieved_at TEXT,
                    payload_json TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE (
                        company_name_key, ticker, fiscal_year,
                        period_type, version
                    )
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_financial_statements_lookup
                ON financial_statement_versions (
                    company_name_key, fiscal_year, version DESC
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_financial_statements_ticker
                ON financial_statement_versions (ticker, fiscal_year, version DESC)
                """
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO schema_migrations (version, applied_at)
                VALUES (?, ?)
                """,
                (SCHEMA_VERSION, self._utc_now()),
            )

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _period_type(metadata: dict[str, Any]) -> str:
        value = str(metadata.get("period_type", "FY")).strip().upper()
        if value not in {"FY", "Q", "TTM", "OTHER"}:
            raise RepositoryError(f"Unsupported financial period_type: {value}")
        return value

    @staticmethod
    def _serialize(statements: FinancialStatements) -> str:
        try:
            return json.dumps(
                asdict(statements),
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
                default=str,
            )
        except (TypeError, ValueError) as exc:
            raise RepositoryError(f"Could not serialize financial statements: {exc}") from exc

    @staticmethod
    def _deserialize(payload: str) -> FinancialStatements:
        try:
            data = json.loads(payload)
            periods = [
                PeriodFinancials(
                    period=item["period"],
                    income_statement=IncomeStatement(**item["income_statement"]),
                    balance_sheet=BalanceSheet(**item["balance_sheet"]),
                    cash_flow_statement=CashFlowStatement(**item["cash_flow_statement"]),
                )
                for item in data.get("periods", [])
            ]
            return FinancialStatements(
                company_name=data["company_name"],
                ticker=data["ticker"],
                currency=data["currency"],
                fiscal_year=data["fiscal_year"],
                income_statement=IncomeStatement(**data["income_statement"]),
                balance_sheet=BalanceSheet(**data["balance_sheet"]),
                cash_flow_statement=CashFlowStatement(**data["cash_flow_statement"]),
                periods=periods,
                metadata=data.get("metadata", {}),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RepositoryError(f"Stored financial statement payload is invalid: {exc}") from exc

    def save(self, fs: FinancialStatements) -> int:
        """Append a statement version and return its database record ID."""
        if not fs.company_name.strip() or not fs.ticker.strip():
            raise RepositoryError("Company name and ticker are required for persistence.")
        if not fs.fiscal_year.strip() or not fs.currency.strip():
            raise RepositoryError("Fiscal year and currency are required for persistence.")

        metadata = fs.metadata or {}
        period_type = self._period_type(metadata)
        period_end = metadata.get("period_end")
        source_provider = metadata.get("source_provider") or metadata.get("provider")
        source_type = metadata.get("source_type")
        source_reference = metadata.get("source_reference")
        retrieved_at = metadata.get("retrieved_at")
        source_provider = str(source_provider) if source_provider is not None else None
        source_type = str(source_type) if source_type is not None else None
        source_reference = str(source_reference) if source_reference is not None else None
        retrieved_at = str(retrieved_at) if retrieved_at is not None else None
        payload = self._serialize(fs)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        company_key = fs.company_name.casefold().strip()

        try:
            with self._connection() as connection:
                row = connection.execute(
                    """
                    SELECT COALESCE(MAX(version), 0) AS current_version
                    FROM financial_statement_versions
                    WHERE company_name_key = ? AND ticker = ?
                      AND fiscal_year = ? AND period_type = ?
                    """,
                    (company_key, fs.ticker.strip().upper(), fs.fiscal_year.strip(), period_type),
                ).fetchone()
                version = int(row["current_version"]) + 1
                cursor = connection.execute(
                    """
                    INSERT INTO financial_statement_versions (
                        company_name, company_name_key, ticker, fiscal_year,
                        period_end, period_type, currency, version,
                        source_provider, source_type, source_reference,
                        retrieved_at, payload_json, content_sha256, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        fs.company_name.strip(),
                        company_key,
                        fs.ticker.strip().upper(),
                        fs.fiscal_year.strip(),
                        str(period_end) if period_end is not None else None,
                        period_type,
                        fs.currency.strip().upper(),
                        version,
                        source_provider,
                        source_type,
                        source_reference,
                        retrieved_at,
                        payload,
                        digest,
                        self._utc_now(),
                    ),
                )
                return int(cursor.lastrowid)
        except sqlite3.Error as exc:
            raise RepositoryError(f"Could not persist financial statements: {exc}") from exc

    def store(self, fs: FinancialStatements) -> int:
        """Backward-compatible alias for save()."""
        return self.save(fs)

    def get(self, company_name: str, fiscal_year: str) -> FinancialStatements:
        """Return the latest version for a company and fiscal year."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT payload_json FROM financial_statement_versions
                WHERE company_name_key = ? AND fiscal_year = ?
                ORDER BY version DESC, id DESC LIMIT 1
                """,
                (company_name.casefold().strip(), fiscal_year.strip()),
            ).fetchone()
        if row is None:
            raise RepositoryError(
                f"Financial statements not found for Company: '{company_name}', "
                f"Period: '{fiscal_year}'"
            )
        return self._deserialize(row["payload_json"])

    def load(self, company_name: str, fiscal_year: str) -> FinancialStatements:
        """Backward-compatible alias for get()."""
        return self.get(company_name, fiscal_year)

    def exists(self, company_name: str, fiscal_year: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT 1 FROM financial_statement_versions
                WHERE company_name_key = ? AND fiscal_year = ? LIMIT 1
                """,
                (company_name.casefold().strip(), fiscal_year.strip()),
            ).fetchone()
        return row is not None

    def list(
        self, company_name: str | None = None, ticker: str | None = None
    ) -> list[FinancialStatements]:
        """List the latest stored version of each company/period combination."""
        clauses: list[str] = []
        parameters: list[str] = []
        if company_name:
            clauses.append("company_name_key = ?")
            parameters.append(company_name.casefold().strip())
        if ticker:
            clauses.append("ticker = ?")
            parameters.append(ticker.strip().upper())
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"""
            SELECT payload_json FROM (
                SELECT payload_json,
                       ROW_NUMBER() OVER (
                           PARTITION BY company_name_key, ticker, fiscal_year, period_type
                           ORDER BY version DESC, id DESC
                       ) AS row_number
                FROM financial_statement_versions
                {where}
            )
            WHERE row_number = 1
            ORDER BY json_extract(payload_json, '$.company_name'),
                     json_extract(payload_json, '$.fiscal_year')
        """
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._deserialize(row["payload_json"]) for row in rows]

    def list_versions(self, company_name: str, fiscal_year: str) -> list[dict[str, Any]]:
        """Return immutable version metadata, newest first."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, ticker, fiscal_year, period_end, period_type,
                       currency, version, source_provider, source_type,
                       source_reference, retrieved_at, content_sha256, created_at
                FROM financial_statement_versions
                WHERE company_name_key = ? AND fiscal_year = ?
                ORDER BY version DESC, id DESC
                """,
                (company_name.casefold().strip(), fiscal_year.strip()),
            ).fetchall()
        return [dict(row) for row in rows]

    def clear(self) -> None:
        """Clear records for isolated tests only; never used by application code."""
        if os.getenv("PYTEST_CURRENT_TEST") is None:
            raise RepositoryError("clear() is restricted to active pytest execution.")
        with self._connect() as connection:
            connection.execute("DELETE FROM financial_statement_versions")
