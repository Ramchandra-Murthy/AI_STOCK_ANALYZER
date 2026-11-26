"""
==========================================================
EQUITY VALUATION PLATFORM v5.1
Module  : services.forecast.revenue_forecast
Layer   : Services / Forecast / Subservices
Summary : Revenue Projection Subservice supporting CAGR, Linear
          Regression, Rolling Average, and Guidance Overrides.
==========================================================
"""

from __future__ import annotations

from typing import Any

from core.logger import logger
from services.forecast.algorithms.cagr import CAGRForecastEngine
from services.forecast.algorithms.linear_regression import LinearRegressionForecastEngine
from services.forecast.algorithms.rolling_average import RollingAverageForecastEngine
from services.forecast.exceptions import ForecastConfigurationError
from services.forecast.forecast_input import ForecastInput
from services.forecast.forecast_models import (
    ConfidenceLevel,
    ForecastMethod,
    RevenueForecast,
)


class RevenueForecastEngine:
    """Subservice orchestrator for top-line revenue projections."""

    def __init__(self) -> None:
        self._cagr_algo = CAGRForecastEngine()
        self._rolling_avg_algo = RollingAverageForecastEngine()
        self._linear_regression_algo = LinearRegressionForecastEngine()

    def forecast_revenue(
        self,
        inp: ForecastInput,
        method: ForecastMethod | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> RevenueForecast:
        """Projects future top-line revenue series given historical inputs and strategy choice."""
        symbol = inp.symbol
        selected_method = method or inp.method or ForecastMethod.CAGR
        logger.info(
            f"[REVENUE FORECAST] Projecting revenues for {symbol} via method: {selected_method}"
        )

        # 1. Check for Management Guidance Override
        if inp.management_guidance_revenue is not None:
            logger.info(f"[REVENUE FORECAST] Applying management guidance override for {symbol}")
            projected = tuple(inp.management_guidance_revenue)
            hist_revenues = tuple(inp.historical_revenues)
            growth_rates = tuple(
                round((curr - prev) / prev, 4) if prev != 0 else 0.0
                for prev, curr in zip(hist_revenues[-1:] + projected[:-1], projected, strict=False)
            )
            return RevenueForecast(
                historical=hist_revenues,
                projected=projected,
                growth_rates=growth_rates,
                method=ForecastMethod.MANAGEMENT_GUIDANCE,
                confidence=ConfidenceLevel.HIGH,
            )

        # 2. Dispatch to the concrete calculation interface shared by the algorithms.
        hist_tuple = tuple(inp.historical_revenues)
        if selected_method == ForecastMethod.LINEAR_REGRESSION:
            algorithm = self._linear_regression_algo
            method_used = ForecastMethod.LINEAR_REGRESSION
        elif selected_method == ForecastMethod.ROLLING_AVERAGE:
            algorithm = self._rolling_avg_algo
            method_used = ForecastMethod.ROLLING_AVERAGE
        elif selected_method == ForecastMethod.CAGR:
            algorithm = self._cagr_algo
            method_used = ForecastMethod.CAGR
        else:
            raise ForecastConfigurationError(
                f"Forecast method '{selected_method}' is not supported by the legacy "
                "revenue forecast engine."
            )

        projected_series = algorithm.calculate(hist_tuple, inp.forecast_years)

        # 4. Compute growth rate series safely handling tuple conversion
        growth_rates = tuple(
            round((curr - prev) / prev, 4) if prev != 0 else 0.0
            for prev, curr in zip(
                hist_tuple[-1:] + projected_series[:-1], projected_series, strict=False
            )
        )

        return RevenueForecast(
            historical=hist_tuple,
            projected=projected_series,
            growth_rates=growth_rates,
            method=method_used,
            confidence=ConfidenceLevel.HIGH,
        )
