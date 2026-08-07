from __future__ import annotations

import logging
from typing import Dict, Any, List
from services.fundamentals.canonical_models import CanonicalIncomeStatement, CanonicalBalanceSheet, CanonicalCashFlowStatement

logger = logging.getLogger(__name__)

class CanonicalFinancialValidator:
    """Performs rigorous accounting identity and sanity checks on canonical financial statements."""

    @staticmethod
    def validate_balance_sheet(bs: CanonicalBalanceSheet) -> List[str]:
        errors = []
        # Accounting Identity: Assets = Liabilities + Equity
        calculated_liab_equity = bs.total_liabilities + bs.shareholders_equity
        if abs(bs.total_assets - calculated_liab_equity) > (bs.total_assets * 0.05 + 1.0):
            errors.append(f"Balance Sheet identity violation: Total Assets ({bs.total_assets}) != Liabilities ({bs.total_liabilities}) + Equity ({bs.shareholders_equity})")
        if bs.total_assets < 0:
            errors.append("Total Assets cannot be negative.")
        return errors

    @staticmethod
    def validate_income_statement(inc: CanonicalIncomeStatement) -> List[str]:
        errors = []
        if inc.revenue < 0:
            errors.append("Revenue cannot be negative.")
        if inc.shares_outstanding < 0:
            errors.append("Shares outstanding cannot be negative.")
        return errors

    @staticmethod
    def compute_analytics(bs: CanonicalBalanceSheet, inc: CanonicalIncomeStatement, cf: CanonicalCashFlowStatement) -> Dict[str, float]:
        """Computes enterprise value components, net debt, invested capital, working capital, and core analytics."""
        total_debt = bs.short_term_debt + bs.current_portion_long_term_debt + bs.long_term_debt
        cash_and_equivalents = bs.cash + bs.cash_equivalents + bs.short_term_investments
        net_debt = total_debt - cash_and_equivalents
        working_capital = bs.total_current_assets - bs.total_current_liabilities
        invested_capital = bs.total_assets - bs.total_current_liabilities
        tangible_book_value = bs.shareholders_equity - bs.goodwill - bs.intangible_assets

        return {
            "total_debt": total_debt,
            "cash_and_equivalents": cash_and_equivalents,
            "net_debt": net_debt,
            "working_capital": working_capital,
            "invested_capital": invested_capital,
            "tangible_book_value": tangible_book_value,
            "free_cash_flow": cf.free_cash_flow if cf.free_cash_flow != 0.0 else cf.operating_cash_flow - abs(cf.capital_expenditures)
        }
