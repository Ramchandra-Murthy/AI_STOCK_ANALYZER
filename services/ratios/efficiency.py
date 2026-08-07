from __future__ import annotations

import logging
from typing import Dict, Any
from services.fundamentals.canonical_models import CanonicalIncomeStatement, CanonicalBalanceSheet
from services.ratios.models import RatioCategoryResult

logger = logging.getLogger(__name__)

class EfficiencyRatioEngine:
    """Computes asset turnover, working capital efficiency, and cash conversion cycle metrics."""

    @staticmethod
    def compute(inc: CanonicalIncomeStatement, bs: CanonicalBalanceSheet, symbol: str = "UNKNOWN") -> RatioCategoryResult:
        logger.info("Computing efficiency ratios for %s (%s)", symbol, inc.period)
        
        rev = max(inc.revenue, 1.0)
        cogs = max(inc.cost_of_revenue, 1.0)
        assets = max(bs.total_assets, 1.0)
        inventory = bs.inventory
        receivables = bs.accounts_receivable
        payables = bs.accounts_payable

        asset_turnover = round(rev / assets, 2)
        inventory_turnover = round(cogs / max(inventory, 1.0), 2)
        inventory_days = round(365.0 / inventory_turnover, 1)
        receivable_turnover = round(rev / max(receivables, 1.0), 2)
        receivable_days = round(365.0 / receivable_turnover, 1)
        payable_turnover = round(cogs / max(payables, 1.0), 2)
        payable_days = round(365.0 / payable_turnover, 1)
        cash_conversion_cycle = round(inventory_days + receivable_days - payable_days, 1)

        metrics = {
            "asset_turnover": asset_turnover,
            "inventory_turnover": inventory_turnover,
            "inventory_days": inventory_days,
            "receivable_turnover": receivable_turnover,
            "receivable_days": receivable_days,
            "payable_turnover": payable_turnover,
            "payable_days": payable_days,
            "cash_conversion_cycle": cash_conversion_cycle
        }

        return RatioCategoryResult(
            category_name="Efficiency",
            symbol=symbol,
            period=inc.period,
            metrics=metrics,
            metadata={"version": "7.0", "standard": "CFA/McKinsey"}
        )
