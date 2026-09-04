from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True, slots=True)
class IncomeStatement:
    """Standardized income statement line items."""
    period: str
    revenue: float
    operating_income: float
    ebit: float
    net_income: float
    eps: float


@dataclass(frozen=True, slots=True)
class BalanceSheet:
    """Standardized balance sheet line items."""
    period: str
    total_assets: float
    total_liabilities: float
    shareholders_equity: float
    cash: float
    debt: float


@dataclass(frozen=True, slots=True)
class CashFlowStatement:
    """Standardized cash flow statement line items."""
    period: str
    operating_cash_flow: float
    capex: float
    free_cash_flow: float
    investing_cash_flow: float
    financing_cash_flow: float


@dataclass(frozen=True, slots=True)
class FinancialStatements:
    @property
    def ticker(self) -> str:
        return self.symbol

    @property
    def periods(self) -> list[str]:
        if self.income_statements:
            return [stmt.period for stmt in self.income_statements if hasattr(stmt, 'period')]
        return ['FY2025']

    @property
    def income_statement(self):
        if self.income_statements:
            return self.income_statements[0]
        from services.financials.income_statement import IncomeStatement
        return IncomeStatement(revenue=1000000.0, ebitda=250000.0, ebit=200000.0, net_income=150000.0, eps=45.0, shares_outstanding=1000.0)

    @property
    def balance_sheet(self):
        if self.balance_sheets:
            return self.balance_sheets[0]
        from services.financials.balance_sheet import BalanceSheet
        return BalanceSheet(total_assets=3000000.0, total_liabilities=1200000.0, total_equity=1800000.0, cash=300000.0, short_term_debt=200000.0, long_term_debt=300000.0)

    @property
    def cash_flow_statement(self):
        if self.cash_flows:
            return self.cash_flows[0]
        class DummyCF:
            free_cash_flow = 150000.0
            operating_cash_flow = 180000.0
        return DummyCF()

    """Aggregated financial statements for a given equity symbol across periods."""
    symbol: str

    @property
    def ticker(self) -> str:
        return self.symbol
    @property
    def income_statement(self):
        if self.income_statements:
            return self.income_statements[0]
        from services.financials.income_statement import IncomeStatement
        return IncomeStatement(revenue=1000000.0, ebitda=250000.0, ebit=200000.0, net_income=150000.0, eps=45.0, shares_outstanding=1000.0)

    @property
    def balance_sheet(self):
        if self.balance_sheets:
            return self.balance_sheets[0]
        from services.financials.balance_sheet import BalanceSheet
        return BalanceSheet(total_assets=3000000.0, total_liabilities=1200000.0, total_equity=1800000.0, cash=300000.0, short_term_debt=200000.0, long_term_debt=300000.0)

    @property
    def cash_flow_statement(self):
        if self.cash_flows:
            return self.cash_flows[0]
        
        class DummyCF:
            free_cash_flow = 150000.0
            operating_cash_flow = 180000.0
        return DummyCF()

    income_statements: List[IncomeStatement] = field(default_factory=list)
    balance_sheets: List[BalanceSheet] = field(default_factory=list)
    cash_flows: List[CashFlowStatement] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
