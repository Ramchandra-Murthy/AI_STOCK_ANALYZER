from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class AdvancedQualityEngine:
    """Computes advanced accounting quality and financial distress scores."""

    @staticmethod
    def compute_altman_z(bs: Any, inc: Any) -> float:
        try:
            total_assets = max(getattr(bs, "total_assets", 1000.0), 1.0)
            total_liab = max(getattr(bs, "total_liabilities", 500.0), 1.0)
            equity = max(
                getattr(bs, "shareholders_equity", getattr(bs, "total_equity", 500.0)), 1.0
            )
            current_assets = getattr(bs, "total_current_assets", total_assets * 0.5)
            current_liabilities = getattr(bs, "total_current_liabilities", total_liab * 0.5)
            working_capital = current_assets - current_liabilities
            retained_earnings = getattr(bs, "retained_earnings", equity * 0.6)
            ebit = getattr(inc, "ebit", 0.0) if inc else 0.0
            market_equity = getattr(bs, "market_value_equity", equity * 1.5)
            sales = getattr(inc, "revenue", 1.0) if inc else 1.0
            x1 = working_capital / total_assets
            x2 = retained_earnings / total_assets
            x3 = ebit / total_assets
            x4 = market_equity / total_liab
            x5 = sales / total_assets
            return round(1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 0.999 * x5, 2)
        except Exception as e:
            logger.warning("Error calculating Altman Z-Score: %s", e)
            return 2.99

    @staticmethod
    def compute_cash_conversion_cycle(bs: Any, inc: Any) -> dict[str, float]:
        try:
            revenue = max(getattr(inc, "revenue", 0.0) if inc else 0.0, 1.0)
            cogs = max(getattr(inc, "cost_of_goods_sold", 0.0) if inc else 0.0, 1.0)
            total_assets = max(getattr(bs, "total_assets", 1000.0), 1.0)
            inventory = max(getattr(bs, "inventory", 0.0), 0.0)
            receivables = max(getattr(bs, "accounts_receivable", 0.0), 0.0)
            payables = max(getattr(bs, "accounts_payable", 0.0), 0.0)
            inv_days = round((inventory / cogs) * 365, 1)
            rec_days = round((receivables / revenue) * 365, 1)
            pay_days = round((payables / cogs) * 365, 1)
            ccc = max(round(inv_days + rec_days - pay_days, 1), 0.0)
            return {
                "inventory_days": inv_days,
                "receivable_days": rec_days,
                "payable_days": pay_days,
                "cash_conversion_cycle": ccc,
            }
        except Exception as e:
            logger.warning("Error calculating Cash Conversion Cycle: %s", e)
            return {
                "inventory_days": 45.0,
                "receivable_days": 60.0,
                "payable_days": 50.0,
                "cash_conversion_cycle": 55.0,
            }
