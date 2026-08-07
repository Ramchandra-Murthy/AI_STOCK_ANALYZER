from __future__ import annotations

import logging
from typing import Dict, Any
from services.fundamentals.canonical_models import CanonicalIncomeStatement, CanonicalBalanceSheet
from services.ratios.models import RatioCategoryResult

logger = logging.getLogger(__name__)

class LiquidityRatioEngine:
    """Computes short-term liquidity and working capital coverage metrics from canonical statements."""

    @staticmethod
    def compute(inc: CanonicalIncomeStatement, bs: CanonicalBalanceSheet, symbol: str = "UNKNOWN") -> RatioCategoryResult:
        logger.info("Computing liquidity ratios for %s (%s)", symbol, inc.period)
        
        ca = max(bs.total_current_assets, 1.0)
        cl = max(bs.total_current_liabilities, 1.0)
        cash = bs.cash + bs.cash_equivalents + bs.short_term_investments
        inventory = bs.inventory
        receivables = bs.accounts_receivable

        current_ratio = round(ca / cl, 2)
        quick_ratio = round((ca - inventory) / cl, 2)
        cash_ratio = round(cash / cl, 2)
        working_capital_ratio = round((ca - cl) / max(bs.total_assets, 1.0), 2)
        defensive_interval = round((cash + receivables) / max(inc.cost_of_revenue / 365.0, 1.0), 1)

        metrics = {
            "current_ratio": current_ratio,
            "quick_ratio": quick_ratio,
            "cash_ratio": cash_ratio,
            "working_capital_ratio": working_capital_ratio,
            "defensive_interval_days": defensive_interval
        }

        return RatioCategoryResult(
            category_name="Liquidity",
            symbol=symbol,
            period=inc.period,
            metrics=metrics,
            metadata={"version": "7.0", "standard": "CFA/McKinsey"}
        )
