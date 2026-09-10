from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class IncomeStatement:
    """Standardized income statement for one reporting period."""

    period: str = "FY2025"
    revenue: float = 0.0
    operating_income: float = 0.0
    other_operating_income: float = 0.0
    total_operating_income: float = 0.0
    cost_of_goods_sold: float = 0.0
    operating_expenses: float = 0.0
    depreciation_and_amortization: float = 0.0
    ebitda: float = 0.0
    ebit: float = 0.0
    finance_cost: float = 0.0
    finance_income: float = 0.0
    profit_before_tax: float = 0.0
    tax_expense: float = 0.0
    net_income: float = 0.0
    shares_outstanding: float = 0.0
    eps: float = 0.0

    def operating_margin(self) -> float:
        return self.ebit / self.revenue if self.revenue else 0.0

    def ebitda_margin(self) -> float:
        return self.ebitda / self.revenue if self.revenue else 0.0

    def net_margin(self) -> float:
        return self.net_income / self.revenue if self.revenue else 0.0
