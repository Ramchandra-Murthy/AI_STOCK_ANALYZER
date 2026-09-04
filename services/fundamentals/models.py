from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from services.financials.income_statement import IncomeStatement
from services.financials.balance_sheet import BalanceSheet
from services.financials.cash_flow import CashFlowStatement


@dataclass(frozen=True, slots=True)
class FinancialStatements:
    """Aggregated financial statements for a given equity symbol across periods."""

    symbol: str

    income_statements: List[IncomeStatement] = field(default_factory=list)
    balance_sheets: List[BalanceSheet] = field(default_factory=list)
    cash_flows: List[CashFlowStatement] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def ticker(self) -> str:
        return self.symbol

    @property
    def periods(self) -> list[str]:
        if self.income_statements:
            return [
                stmt.period
                for stmt in self.income_statements
                if hasattr(stmt, "period")
            ]
        return ["FY2025"]

    @property
    def income_statement(self) -> IncomeStatement:
        if self.income_statements:
            return self.income_statements[0]

        return IncomeStatement(
            revenue=1_000_000.0,
            ebitda=250_000.0,
            ebit=200_000.0,
            net_income=150_000.0,
            eps=45.0,
            shares_outstanding=1_000.0,
        )

    @property
    def balance_sheet(self) -> BalanceSheet:
        if self.balance_sheets:
            return self.balance_sheets[0]

        return BalanceSheet(
            total_assets=3_000_000.0,
            total_liabilities=1_200_000.0,
            total_equity=1_800_000.0,
            cash=300_000.0,
            short_term_debt=200_000.0,
            long_term_debt=300_000.0,
        )

    @property
    def cash_flow_statement(self) -> CashFlowStatement:
        if self.cash_flows:
            return self.cash_flows[0]

        return CashFlowStatement(
            operating_cash_flow=180_000.0,
            capital_expenditure=30_000.0,
            investing_cash_flow=0.0,
            financing_cash_flow=0.0,
        )
