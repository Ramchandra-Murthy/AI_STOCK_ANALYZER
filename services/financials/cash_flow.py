from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CashFlowStatement:
    """Standardized cash flow statement for one reporting period."""

    period: str = "FY2025"
    net_income: float = 0.0
    depreciation_and_amortization: float = 0.0
    share_based_compensation: float = 0.0
    deferred_tax: float = 0.0
    change_in_working_capital: float = 0.0
    other_operating_items: float = 0.0
    operating_cash_flow: float = 0.0
    capital_expenditure: float = 0.0
    capex: float = 0.0
    acquisitions: float = 0.0
    asset_sales: float = 0.0
    investment_purchases: float = 0.0
    investment_sales: float = 0.0
    investing_cash_flow: float = 0.0
    debt_issued: float = 0.0
    debt_repaid: float = 0.0
    dividends_paid: float = 0.0
    share_repurchases: float = 0.0
    equity_issued: float = 0.0
    financing_cash_flow: float = 0.0
    net_change_in_cash: float = 0.0
    beginning_cash: float = 0.0
    ending_cash: float = 0.0
    free_cash_flow: float = 0.0

    def __post_init__(self) -> None:
        if not self.capex:
            self.capex = self.capital_expenditure
        if not self.capital_expenditure:
            self.capital_expenditure = self.capex
        if not self.free_cash_flow:
            self.free_cash_flow = self.operating_cash_flow - self.capex
