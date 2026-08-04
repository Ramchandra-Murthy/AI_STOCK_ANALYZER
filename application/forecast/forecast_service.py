from __future__ import annotations

from decimal import Decimal
from typing import Tuple
from domain.forecast.models import ForecastMethod, ForecastAssumption, ForecastResult
from domain.forecast.algorithms.cagr import CAGRCalculator

class ForecastApplicationService:
    """Application service orchestrating forecast workflows."""

    def execute_forecast(
        self,
        historical_values: Tuple[Decimal, ...],
        assumption: ForecastAssumption
    ) -> ForecastResult:
        if assumption.method == ForecastMethod.CAGR:
            projected = CAGRCalculator.calculate(historical_values, assumption.periods)
            return ForecastResult(
                historical_values=historical_values,
                projected_values=projected,
                method=ForecastMethod.CAGR
            )
        else:
            raise NotImplementedError(f"Forecast method {assumption.method} is not yet supported.")
