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
    """Aggregated financial statements for a given equity symbol across periods."""
    symbol: str
    income_statements: List[IncomeStatement] = field(default_factory=list)
    balance_sheets: List[BalanceSheet] = field(default_factory=list)
    cash_flows: List[CashFlowStatement] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
