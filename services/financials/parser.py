from __future__ import annotations

"""Normalize, validate, and persist financial statement packages."""

from typing import Any

from services.financials.financial_statement import FinancialStatements
from services.financials.normalization import normalize_financial_statements
from services.financials.repository import FinancialStatementRepository
from services.financials.validator import validate_financial_statements


_repository = FinancialStatementRepository()


def parse_financial_statements(
    *,
    company_name: str,
    ticker: str,
    currency: str,
    fiscal_year: str,
    income_statement: dict[str, Any],
    balance_sheet: dict[str, Any],
    cash_flow: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> FinancialStatements:
    """Normalize, validate, and append a financial statement version.

    Provider acquisition is deliberately outside this function. Callers pass
    already-retrieved raw statement dictionaries and optional provenance.
    """
    statements = normalize_financial_statements(
        company_name=company_name,
        ticker=ticker,
        currency=currency,
        fiscal_year=fiscal_year,
        income_raw=income_statement,
        balance_raw=balance_sheet,
        cashflow_raw=cash_flow,
    )
    if metadata:
        statements.metadata.update(metadata)

    validate_financial_statements(statements)
    _repository.save(statements)
    return statements


def get_financial_statements(
    company_name: str,
    fiscal_year: str,
) -> FinancialStatements:
    """Retrieve the latest persisted version for a company and fiscal year."""
    return _repository.get(company_name, fiscal_year)


def repository() -> FinancialStatementRepository:
    """Return the configured financial statement repository."""
    return _repository
