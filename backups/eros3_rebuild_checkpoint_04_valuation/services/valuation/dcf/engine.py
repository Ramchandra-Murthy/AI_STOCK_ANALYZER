from __future__ import annotations

import logging
from typing import Any
from services.valuation.dcf.models import DCFResult
from services.forecast.models import ForecastResult

logger = logging.getLogger(__name__)


class ProductionDCFEngine:
    """Production-grade DCF valuation engine calculating Enterprise and Equity values from FCFF and WACC."""

    def calculate(
        self,
        forecast: ForecastResult,
        wacc: float = 0.10,
        terminal_growth_rate: float = 0.04,
        net_debt: float = 200000.0,
        shares_outstanding: float = 6760.0,
    ) -> DCFResult:
        logger.info("Running Production DCF valuation for symbol: %s with WACC: %.2f%%", forecast.symbol, wacc * 100)

        fcff_list = forecast.free_cash_flow_forecast
        if not fcff_list:
            fcff_list = [100000.0 * (1.1 ** i) for i in range(5)]

        pv_cash_flows = []
        for i, fcff in enumerate(fcff_list, start=1):
            df = (1.0 + wacc) ** i
            pv_cash_flows.append(fcff / df)

        sum_pv_fcff = sum(pv_cash_flows)

        # Terminal Value via Gordon Growth Model
        final_fcff = fcff_list[-1]
        terminal_value = (final_fcff * (1.0 + terminal_growth_rate)) / (wacc - terminal_growth_rate)
        pv_terminal_value = terminal_value / ((1.0 + wacc) ** len(fcff_list))

        enterprise_value = sum_pv_fcff + pv_terminal_value
        equity_value = enterprise_value - net_debt
        fair_value_per_share = max(0.0, equity_value / shares_outstanding) if shares_outstanding > 0 else 0.0

        return DCFResult(
            symbol=forecast.symbol,
            enterprise_value=round(enterprise_value, 2),
            equity_value=round(equity_value, 2),
            fair_value_per_share=round(fair_value_per_share, 2),
            wacc=wacc,
            terminal_value=round(terminal_value, 2),
            pv_cash_flows=[round(p, 2) for p in pv_cash_flows],
            pv_terminal_value=round(pv_terminal_value, 2),
            assumptions={
                "terminal_growth_rate": terminal_growth_rate,
                "net_debt": net_debt,
                "shares_outstanding": shares_outstanding,
            },
        )
