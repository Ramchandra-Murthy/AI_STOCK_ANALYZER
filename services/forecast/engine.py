from __future__ import annotations

import logging
from services.forecast.models import ForecastResult, FinancialMetricForecast
from services.market_data.models import MarketDataResponse

logger = logging.getLogger(__name__)


class ForecastEngine:
    """Computes deterministic or AI-assisted financial forecasts from market and fundamental data."""

    def compute(self, market_data: MarketDataResponse) -> ForecastResult:
        """Run multi-year financial projections based on recent historical prices/metrics."""
        logger.info("Running forecast engine for symbol: %s", market_data.symbol)
        
        # Base values derived or mocked from recent price action / baseline
        base_price = market_data.records[-1].close if market_data.records else 2500.0
        
        rev_base = base_price * 100.0
        eps_base = base_price * 0.05
        fcf_base = base_price * 15.0
        ebitda_base = base_price * 25.0

        revenue = FinancialMetricForecast(
            metric_name="Revenue",
            historical_base=rev_base,
            projections=[rev_base * (1.12 ** i) for i in range(1, 4)],
            cagr=12.0
        )
        
        eps = FinancialMetricForecast(
            metric_name="EPS",
            historical_base=eps_base,
            projections=[eps_base * (1.15 ** i) for i in range(1, 4)],
            cagr=15.0
        )

        fcf = FinancialMetricForecast(
            metric_name="FCF",
            historical_base=fcf_base,
            projections=[fcf_base * (1.10 ** i) for i in range(1, 4)],
            cagr=10.0
        )

        ebitda = FinancialMetricForecast(
            metric_name="EBITDA",
            historical_base=ebitda_base,
            projections=[ebitda_base * (1.14 ** i) for i in range(1, 4)],
            cagr=14.0
        )

        return ForecastResult(
            symbol=market_data.symbol,
            revenue=revenue,
            eps=eps,
            fcf=fcf,
            ebitda=ebitda,
            model_type="DeterministicGrowthModel"
        )
