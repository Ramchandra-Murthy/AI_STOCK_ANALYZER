from __future__ import annotations

import logging
from services.forecast.models import ForecastResult, FinancialMetricForecast

logger = logging.getLogger(__name__)


class ForecastEngine:
    """Institutional forecasting engine incorporating historical CAGR and financial projections."""

    def compute(self, symbol: str, historical_revenue: list[float] | None = None) -> ForecastResult:
        """Compute revenue, earnings, and cash flow projections based on historical data or robust baselines."""
        logger.info("Computing institutional financial forecast for symbol: %s", symbol)

        if historical_revenue and len(historical_revenue) >= 2:
            start_val = historical_revenue[0]
            end_val = historical_revenue[-1]
            n_periods = len(historical_revenue) - 1
            cagr = (end_val / start_val) ** (1 / n_periods) - 1 if start_val > 0 else 0.10
        else:
            cagr = 0.115

        base_revenue = historical_revenue[-1] if historical_revenue else 1000.0
        proj_revenue = [base_revenue * (1 + cagr), base_revenue * (1 + cagr)**2, base_revenue * (1 + cagr)**3]
        proj_eps = [10.0 * (1 + cagr), 10.0 * (1 + cagr)**2, 10.0 * (1 + cagr)**3]
        proj_fcf = [base_revenue * 0.15 * (1 + cagr), base_revenue * 0.15 * (1 + cagr)**2, base_revenue * 0.15 * (1 + cagr)**3]
        proj_ebitda = [base_revenue * 0.22 * (1 + cagr), base_revenue * 0.22 * (1 + cagr)**2, base_revenue * 0.22 * (1 + cagr)**3]

        return ForecastResult(
            symbol=symbol,
            revenue=FinancialMetricForecast(metric_name="Revenue", historical_base=base_revenue, projections=proj_revenue, cagr=cagr),
            eps=FinancialMetricForecast(metric_name="EPS", historical_base=10.0, projections=proj_eps, cagr=cagr),
            fcf=FinancialMetricForecast(metric_name="FCF", historical_base=base_revenue * 0.15, projections=proj_fcf, cagr=cagr),
            ebitda=FinancialMetricForecast(metric_name="EBITDA", historical_base=base_revenue * 0.22, projections=proj_ebitda, cagr=cagr),
            model_type="CAGRDeterministicModel"
        )
