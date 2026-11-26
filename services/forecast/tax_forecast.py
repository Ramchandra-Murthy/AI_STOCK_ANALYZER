"""Tax-rate projection subservice for legacy forecast inputs.

TaxForecast.projected contains effective tax-rate fractions, never currency
amounts. Tax expense is calculated downstream as EBIT multiplied by this rate.
"""
from __future__ import annotations

from math import isfinite
from typing import Any

from core.logger import logger
from services.forecast.exceptions import ForecastConfigurationError
from services.forecast.forecast_input import ForecastInput
from services.forecast.models import ConfidenceLevel, ForecastMethod, TaxForecast


class TaxForecastEngine:
    """Project effective tax rates from matched historical tax and PBT data."""

    def forecast_tax(
        self,
        inp: ForecastInput,
        method: ForecastMethod | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> TaxForecast:
        logger.info("[TAX FORECAST] Projecting tax rates for %s", inp.symbol)
        historical_rates = tuple(
            tax / pbt
            for tax, pbt in zip(inp.historical_tax, inp.historical_pbt, strict=False)
            if pbt > 0 and isfinite(tax) and isfinite(pbt) and 0.0 <= tax / pbt <= 1.0
        )
        if historical_rates:
            effective_rate = sum(historical_rates) / len(historical_rates)
        elif inp.tax_rate_assumption is not None:
            effective_rate = float(inp.tax_rate_assumption)
        else:
            raise ForecastConfigurationError(
                "A tax_rate_assumption is required when no valid positive-PBT "
                "historical effective tax rate is available."
            )

        return TaxForecast(
            historical=historical_rates,
            projected=(effective_rate,) * inp.forecast_years,
            method=method or ForecastMethod.MANUAL,
            confidence=ConfidenceLevel.HIGH,
        )

    # Backward-compatible alias; projected values are tax rates, not tax expense.
    forecast_tax_rate = forecast_tax
