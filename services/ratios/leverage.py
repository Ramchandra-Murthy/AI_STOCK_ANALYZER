from __future__ import annotations

import logging
from typing import Dict, Any
from services.fundamentals.canonical_models import CanonicalIncomeStatement, CanonicalBalanceSheet
from services.ratios.models import RatioCategoryResult

logger = logging.getLogger(__name__)

class LeverageRatioEngine:
    """Computes long-term solvency, leverage, and debt coverage ratios from canonical statements."""

    @staticmethod
    def compute(inc: CanonicalIncomeStatement, bs: CanonicalBalanceSheet, symbol: str = "UNKNOWN") -> RatioCategoryResult:
        logger.info("Computing leverage ratios for %s (%s)", symbol, inc.period)
        
        total_debt = bs.short_term_debt + bs.current_portion_long_term_debt + bs.long_term_debt
        equity = max(bs.shareholders_equity, 1.0)
        assets = max(bs.total_assets, 1.0)
        cash = bs.cash + bs.cash_equivalents + bs.short_term_investments
        net_debt = total_debt - cash
        ebitda = max(inc.ebitda if inc.ebitda else inc.operating_income, 1.0)
        ebit = max(inc.ebit if inc.ebit else inc.operating_income, 1.0)
        interest_exp = max(inc.interest_expense, 1.0)

        debt_to_equity = round(total_debt / equity, 2)
        debt_to_assets = round(total_debt / assets, 2)
        debt_to_capital = round(total_debt / max(total_debt + equity, 1.0), 2)
        net_debt_to_ebitda = round(net_debt / ebitda, 2)
        interest_coverage = round(ebit / interest_exp, 2)
        equity_multiplier = round(assets / equity, 2)

        metrics = {
            "debt_to_equity": debt_to_equity,
            "debt_to_assets": debt_to_assets,
            "debt_to_capital": debt_to_capital,
            "net_debt_to_ebitda": net_debt_to_ebitda,
            "interest_coverage": interest_coverage,
            "equity_multiplier": equity_multiplier
        }

        return RatioCategoryResult(
            category_name="Leverage",
            symbol=symbol,
            period=inc.period,
            metrics=metrics,
            metadata={"version": "7.0", "standard": "CFA/McKinsey"}
        )
