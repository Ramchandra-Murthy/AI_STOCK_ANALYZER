"""
==========================================================
EQUITY VALUATION PLATFORM v5.1
Module  : services.forecast.depreciation_forecast
Layer   : Services / Forecast / Subservices
Summary : Depreciation & Amortization Forecast Subservice.
==========================================================
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

from core.logger import logger
from services.forecast.forecast_input import ForecastInput
from services.forecast.models import (
    ConfidenceLevel,
    DepreciationForecast,
    ForecastMethod,
)


class DepreciationForecastEngine:
    """Subservice orchestrator for D&A projections."""

    def forecast_depreciation(
        self,
        inp: ForecastInput,
        method: Optional[ForecastMethod] = None,
        projected_revenues: Optional[Tuple[float, ...]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> DepreciationForecast:
        """Projects future D&A schedule based on revenue ratio or historical trend."""
        symbol = inp.symbol
        logger.info(f"[DEPRECIATION FORECAST] Projecting D&A for {symbol}")

        if inp.historical_depreciation is not None and inp.historical_revenues:
            ratios = tuple(
                dep / rev if rev != 0 else 0.02
                for dep, rev in zip(
                    inp.historical_depreciation, inp.historical_revenues
                )
            )
            dep_ratio = sum(ratios) / len(ratios) if ratios else 0.02
        else:
            dep_ratio = 0.02  # Benchmark default

        if projected_revenues is not None:
            projected = tuple(round(rev * dep_ratio, 4) for rev in projected_revenues)
        else:
            last_dep = (
                inp.historical_depreciation[-1] if inp.historical_depreciation else 5.0
            )
            projected = (round(last_dep, 4),) * inp.forecast_years

        return DepreciationForecast(
            historical=inp.historical_depreciation or (),
            projected=projected,
            method=method or inp.method or ForecastMethod.CAGR,
            confidence=ConfidenceLevel.MEDIUM,
        )
