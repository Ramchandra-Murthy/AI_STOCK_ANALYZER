from __future__ import annotations

import logging

from services.fundamentals.canonical_models import (
    CanonicalBalanceSheet,
    CanonicalIncomeStatement,
)
from services.ratios.models import RatioCategoryResult

logger = logging.getLogger(__name__)


class ProfitabilityRatioEngine:
    """Computes comprehensive profitability and return on capital metrics from canonical statements."""

    @staticmethod
    def compute(
        inc: CanonicalIncomeStatement, bs: CanonicalBalanceSheet, symbol: str = "UNKNOWN"
    ) -> RatioCategoryResult:
        logger.info("Computing profitability ratios for %s (%s)", symbol, inc.period)

        rev = max(inc.revenue, 1.0)
        equity = max(bs.shareholders_equity, 1.0)
        assets = max(bs.total_assets, 1.0)
        invested_capital = max(bs.total_assets - bs.total_current_liabilities, 1.0)

        gross_margin = (
            round((inc.gross_profit / rev) * 100.0, 2)
            if inc.gross_profit
            else round(((rev - inc.cost_of_revenue) / rev) * 100.0, 2)
        )
        operating_margin = round((inc.operating_income / rev) * 100.0, 2)
        net_margin = round((inc.net_income / rev) * 100.0, 2)
        ebitda_margin = round((inc.ebitda / rev) * 100.0, 2) if inc.ebitda else operating_margin

        roe = round((inc.net_income / equity) * 100.0, 2)
        roa = round((inc.net_income / assets) * 100.0, 2)
        roic = (
            round((inc.ebit / invested_capital) * 100.0, 2)
            if inc.ebit
            else round((inc.operating_income / invested_capital) * 100.0, 2)
        )
        roce = round((inc.ebit / invested_capital) * 100.0, 2)

        metrics = {
            "gross_margin": gross_margin,
            "operating_margin": operating_margin,
            "net_margin": net_margin,
            "ebitda_margin": ebitda_margin,
            "roe": roe,
            "roa": roa,
            "roic": roic,
            "roce": roce,
        }

        return RatioCategoryResult(
            category_name="Profitability",
            symbol=symbol,
            period=inc.period,
            metrics=metrics,
            metadata={"version": "7.0", "standard": "CFA/McKinsey"},
        )
