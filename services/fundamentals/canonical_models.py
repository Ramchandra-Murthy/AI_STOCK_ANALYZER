from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass(frozen=True)
class CanonicalIncomeStatement:
    period: str
    revenue: float
    other_revenue: float = 0.0
    total_revenue: float = 0.0
    cost_of_revenue: float = 0.0
    gross_profit: float = 0.0
    gross_margin: float = 0.0
    research_development: float = 0.0
    sales_marketing: float = 0.0
    general_administrative: float = 0.0
    operating_expenses: float = 0.0
    operating_income: float = 0.0
    ebitda: float = 0.0
    ebit: float = 0.0
    interest_expense: float = 0.0
    pretax_income: float = 0.0
    tax_expense: float = 0.0
    net_income: float = 0.0
    eps: float = 0.0
    diluted_eps: float = 0.0
    shares_outstanding: float = 0.0
    diluted_shares: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class CanonicalBalanceSheet:
    period: str
    cash: float = 0.0
    cash_equivalents: float = 0.0
    short_term_investments: float = 0.0
    accounts_receivable: float = 0.0
    inventory: float = 0.0
    other_current_assets: float = 0.0
    total_current_assets: float = 0.0
    property_plant_equipment: float = 0.0
    goodwill: float = 0.0
    intangible_assets: float = 0.0
    long_term_investments: float = 0.0
    deferred_tax_assets: float = 0.0
    total_assets: float = 0.0
    accounts_payable: float = 0.0
    accrued_expenses: float = 0.0
    short_term_debt: float = 0.0
    current_portion_long_term_debt: float = 0.0
    other_current_liabilities: float = 0.0
    total_current_liabilities: float = 0.0
    long_term_debt: float = 0.0
    deferred_tax_liabilities: float = 0.0
    total_liabilities: float = 0.0
    common_stock: float = 0.0
    additional_paid_in_capital: float = 0.0
    retained_earnings: float = 0.0
    treasury_stock: float = 0.0
    minority_interest: float = 0.0
    shareholders_equity: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class CanonicalCashFlowStatement:
    period: str
    operating_cash_flow: float = 0.0
    net_income: float = 0.0
    depreciation: float = 0.0
    amortization: float = 0.0
    stock_compensation: float = 0.0
    deferred_taxes: float = 0.0
    change_in_receivables: float = 0.0
    change_in_inventory: float = 0.0
    change_in_payables: float = 0.0
    capital_expenditures: float = 0.0
    acquisitions: float = 0.0
    investments_purchased: float = 0.0
    investments_sold: float = 0.0
    debt_issued: float = 0.0
    debt_repaid: float = 0.0
    share_buybacks: float = 0.0
    dividends: float = 0.0
    equity_issued: float = 0.0
    free_cash_flow: float = 0.0
    owner_earnings: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
