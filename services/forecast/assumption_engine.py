"""
==========================================================
ASSUMPTION ENGINE
Module  : services.forecast.assumption_engine
Layer   : Domain / Forecast
==========================================================
"""

from __future__ import annotations

import logging
from typing import Any

from services.forecast.models import ForecastAssumption, ForecastMethod

logger = logging.getLogger(__name__)


class AssumptionEngine:
    """Engine for deriving forward-looking financial assumptions."""

    @staticmethod
    def derive_assumptions(
        historical_revenue: tuple[float, ...],
        historical_margins: tuple[float, ...],
        historical_capex: tuple[float, ...],
        method: ForecastMethod = ForecastMethod.CAGR,
        **kwargs: Any,
    ) -> ForecastAssumption:
        """Derives baseline assumptions from historical data streams."""
        logger.info(f"Deriving baseline assumptions using method: {method.value}")

        rev_growth = (
            0.08
            if len(historical_revenue) < 2
            else (historical_revenue[-1] - historical_revenue[0])
            / historical_revenue[0]
        )
        ebitda_m = historical_margins[-1] if historical_margins else 0.15
        tax_r = 0.25
        capex_pct = (
            0.05
            if not historical_capex
            or not historical_revenue
            or historical_revenue[-1] == 0
            else abs(historical_capex[-1] / historical_revenue[-1])
        )
        wc_pct = 0.10

        return ForecastAssumption(
            revenue_growth_rate=rev_growth,
            ebitda_margin=ebitda_m,
            tax_rate=tax_r,
            capex_pct_revenue=capex_pct,
            working_capital_pct_revenue=wc_pct,
            metadata={"engine": "AssumptionEngine", "method": method.value},
        )
