"""
==========================================================
EQUITY VALUATION PLATFORM v5.1
Module  : services.forecast.margin_forecast
Layer   : Services / Forecast / Subservices
Summary : Operating Margin (EBIT) Forecast Subservice executing
          historical mean and mean-reversion decay.
==========================================================
"""

from __future__ import annotations

from typing import Any

from core.logger import logger
from services.forecast.algorithms.mean_reversion import MeanReversionCalculator
from services.forecast.exceptions import ForecastConfigurationError
from services.forecast.forecast_input import ForecastInput
from services.forecast.forecast_models import (
    ConfidenceLevel,
    ForecastMethod,
    MarginForecast,
)


class MarginForecastEngine:
    """Subservice orchestrator for operating margin projections."""

    def __init__(self) -> None:
        self._mean_reversion_algo = MeanReversionCalculator()

    def forecast_margins(
        self,
        inp: ForecastInput,
        method: ForecastMethod | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> MarginForecast:
        """Calculates future EBIT margins based on historical ratio history."""
        symbol = inp.symbol
        logger.info(f"[MARGIN FORECAST] Projecting operating margins for {symbol}")

        # Compute historical EBIT margins
        if inp.historical_ebits is not None:
            historical_margins = tuple(
                ebit / rev if rev != 0 else 0.0
                for ebit, rev in zip(inp.historical_ebits, inp.historical_revenues, strict=False)
            )
        else:
            historical_margins = (0.15,) * len(inp.historical_revenues)

        mean_margin = (
            sum(historical_margins) / len(historical_margins) if historical_margins else 0.15
        )

        selected_method = method or inp.method

        if selected_method == ForecastMethod.MEAN_REVERSION:
            projected = self._mean_reversion_algo.project(historical_margins, inp.forecast_years)
            method_used = ForecastMethod.MEAN_REVERSION
        elif selected_method in (ForecastMethod.CAGR, ForecastMethod.HISTORICAL_MEAN):
            projected = (round(mean_margin, 4),) * inp.forecast_years
            method_used = ForecastMethod.HISTORICAL_MEAN
        else:
            raise ForecastConfigurationError(
                f"Forecast method '{selected_method}' is not supported by the legacy "
                "margin forecast engine. Supported methods: HISTORICAL_MEAN, MEAN_REVERSION."
            )

        return MarginForecast(
            historical=historical_margins,
            projected=projected,
            method=method_used,
            confidence=ConfidenceLevel.MEDIUM,
        )
