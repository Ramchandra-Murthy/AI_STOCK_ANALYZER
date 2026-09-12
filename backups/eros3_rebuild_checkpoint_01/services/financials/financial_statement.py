from __future__ import annotations

"""
==========================================================
STANDARD FINANCIAL STATEMENT MODEL
Module  : financial_statement
Version : V1.1
==========================================================

Canonical financial statement container used throughout EROS.
"""

from dataclasses import dataclass, field
from typing import Any

from services.financials.balance_sheet import BalanceSheet
from services.financials.cash_flow import CashFlowStatement
from services.financials.income_statement import IncomeStatement


@dataclass(slots=True)
class PeriodFinancials:
    """Financial statements for a single reporting period."""

    period: str
    income_statement: IncomeStatement
    balance_sheet: BalanceSheet
    cash_flow_statement: CashFlowStatement


@dataclass(slots=True)
class FinancialStatements:
    """Canonical standardized financial statement container."""

    company_name: str
    ticker: str
    currency: str
    fiscal_year: str

    income_statement: IncomeStatement
    balance_sheet: BalanceSheet
    cash_flow_statement: CashFlowStatement

    periods: list[PeriodFinancials] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def symbol(self) -> str:
        """Compatibility alias for callers using symbol terminology."""
        return self.ticker

    @property
    def income_statements(self) -> list[IncomeStatement]:
        """Compatibility view of all income statements."""
        if self.periods:
            return [p.income_statement for p in self.periods]
        return [self.income_statement]

    @property
    def balance_sheets(self) -> list[BalanceSheet]:
        """Compatibility view of all balance sheets."""
        if self.periods:
            return [p.balance_sheet for p in self.periods]
        return [self.balance_sheet]

    @property
    def cash_flows(self) -> list[CashFlowStatement]:
        """Compatibility view of all cash-flow statements."""
        if self.periods:
            return [p.cash_flow_statement for p in self.periods]
        return [self.cash_flow_statement]

    def summary(self) -> dict[str, Any]:
        return {
            "company": self.company_name,
            "ticker": self.ticker,
            "currency": self.currency,
            "year": self.fiscal_year,
            "revenue": self.income_statement.revenue,
            "ebit": self.income_statement.ebit,
            "net_income": self.income_statement.net_income,
            "cash": self.balance_sheet.total_cash,
            "debt": self.balance_sheet.total_debt,
        }
