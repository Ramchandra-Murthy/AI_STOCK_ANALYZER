from __future__ import annotations
from dataclasses import dataclass

@dataclass(slots=True)
class BalanceSheet:
    """Standardized balance sheet for one reporting period."""
    period: str = "FY2025"
    cash: float = 0.0
    cash_equivalents: float = 0.0
    short_term_investments: float = 0.0
    accounts_receivable: float = 0.0
    inventory: float = 0.0
    other_current_assets: float = 0.0
    total_current_assets: float = 0.0
    property_plant_equipment: float = 0.0
    right_of_use_assets: float = 0.0
    goodwill: float = 0.0
    intangible_assets: float = 0.0
    long_term_investments: float = 0.0
    associates_and_joint_ventures: float = 0.0
    deferred_tax_assets: float = 0.0
    other_non_current_assets: float = 0.0
    total_non_current_assets: float = 0.0
    total_assets: float = 0.0
    accounts_payable: float = 0.0
    short_term_debt: float = 0.0
    current_lease_liabilities: float = 0.0
    accrued_expenses: float = 0.0
    other_current_liabilities: float = 0.0
    total_current_liabilities: float = 0.0
    long_term_debt: float = 0.0
    long_term_lease_liabilities: float = 0.0
    deferred_tax_liabilities: float = 0.0
    pension_liabilities: float = 0.0
    other_non_current_liabilities: float = 0.0
    total_non_current_liabilities: float = 0.0
    total_liabilities: float = 0.0
    share_capital: float = 0.0
    retained_earnings: float = 0.0
    reserves: float = 0.0
    minority_interest: float = 0.0
    total_equity: float = 0.0
    shareholders_equity: float = 0.0
    debt: float = 0.0

    def __post_init__(self) -> None:
        if self.total_equity == 0.0 and self.shareholders_equity != 0.0:
            self.total_equity = self.shareholders_equity
        elif self.shareholders_equity == 0.0 and self.total_equity != 0.0:
            self.shareholders_equity = self.total_equity

    @property
    def total_cash(self) -> float:
        """Canonical total cash resources used by EROS valuation and ratio engines."""
        return self.cash + self.cash_equivalents + self.short_term_investments

    @property
    def total_debt(self) -> float:
        return self.debt if self.debt else self.short_term_debt + self.long_term_debt

    @property
    def net_debt(self) -> float:
        """Canonical net debt used by EROS financial-ratio and valuation engines."""
        return self.total_debt - self.total_cash

    @property
    def current_assets(self) -> float:
        return self.total_current_assets

    @property
    def current_liabilities(self) -> float:
        return self.total_current_liabilities
