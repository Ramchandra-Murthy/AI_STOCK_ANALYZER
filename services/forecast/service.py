"""
Module: services.forecast.service
Description: Institutional orchestrator for financial forecasting workflows.
Author: Engineering Team
Python Version: 3.13+
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from services.forecast.models import (
    ConfidenceLevel,
    ForecastMethod,
    ForecastScenario,
    RevenueForecast,
    MarginForecast,
    CapexForecast,
    DepreciationForecast,
    WorkingCapitalForecast,
    TaxForecast,
    TerminalGrowthForecast,
    ForecastConfidence,
)
from services.forecast.algorithms.cagr import CAGRForecastEngine
from services.forecast.algorithms.linear_regression import (
    LinearRegressionForecastEngine,
)
from services.forecast.algorithms.rolling_average import RollingAverageForecastEngine

logger = logging.getLogger(__name__)


class ForecastService:
    """Orchestration service for generating multi-statement financial projections."""

    def __init__(self) -> None:
        self._cagr_engine = CAGRForecastEngine()
        self._lr_engine = LinearRegressionForecastEngine()
        self._ra_engine = RollingAverageForecastEngine()

    def _get_engine(self, method: ForecastMethod):
        """Maps forecast method enum to its respective computational engine."""
        if method in (
            ForecastMethod.CAGR,
            ForecastMethod.INDUSTRY,
            ForecastMethod.MANAGEMENT_GUIDANCE,
            ForecastMethod.HYBRID,
        ):
            return self._cagr_engine
        elif method in (
            ForecastMethod.LINEAR_REGRESSION,
            ForecastMethod.MEAN_REVERSION,
        ):
            return self._lr_engine
        elif method in (
            ForecastMethod.ROLLING_AVERAGE,
            ForecastMethod.HISTORICAL_MEAN,
            ForecastMethod.EXPONENTIAL_SMOOTHING,
        ):
            return self._ra_engine
        return self._cagr_engine

    def generate_revenue_forecast(
        self,
        historical: Tuple[float, ...],
        periods: int,
        method: ForecastMethod = ForecastMethod.CAGR,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        **kwargs: Any,
    ) -> RevenueForecast:
        """Generates a validated immutable RevenueForecast projection."""
        logger.info(
            f"Generating revenue forecast over {periods} periods using {method.value}"
        )
        engine = self._get_engine(method)
        projected = engine.calculate(historical, periods, **kwargs)

        # Calculate implied year-over-year growth rates for projected period
        growth_rates = []
        combined = historical + projected
        for i in range(len(historical), len(combined)):
            prev = combined[i - 1]
            curr = combined[i]
            rate = (curr / prev - 1.0) if prev != 0 else 0.0
            growth_rates.append(rate)

        return RevenueForecast(
            historical=historical,
            projected=projected,
            method=method,
            confidence=confidence,
            growth_rates=tuple(growth_rates),
        )

    def generate_margin_forecast(
        self,
        historical: Tuple[float, ...],
        periods: int,
        method: ForecastMethod = ForecastMethod.ROLLING_AVERAGE,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        **kwargs: Any,
    ) -> MarginForecast:
        """Generates a validated immutable MarginForecast projection."""
        logger.info(
            f"Generating margin forecast over {periods} periods using {method.value}"
        )
        engine = self._get_engine(method)
        projected = engine.calculate(historical, periods, **kwargs)

        return MarginForecast(
            historical=historical,
            projected=projected,
            method=method,
            confidence=confidence,
        )

    def generate_capex_forecast(
        self,
        historical: Tuple[float, ...],
        periods: int,
        method: ForecastMethod = ForecastMethod.HISTORICAL_MEAN,
        confidence: ConfidenceLevel = ConfidenceLevel.LOW,
        **kwargs: Any,
    ) -> CapexForecast:
        """Generates a validated immutable CapexForecast projection."""
        logger.info(
            f"Generating capex forecast over {periods} periods using {method.value}"
        )
        engine = self._get_engine(method)
        projected = engine.calculate(historical, periods, **kwargs)

        return CapexForecast(
            historical=historical,
            projected=projected,
            method=method,
            confidence=confidence,
        )

    def generate_working_capital_forecast(
        self,
        historical: Tuple[float, ...],
        periods: int,
        method: ForecastMethod = ForecastMethod.ROLLING_AVERAGE,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
        **kwargs: Any,
    ) -> WorkingCapitalForecast:
        """Generates a validated immutable WorkingCapitalForecast projection with deltas."""
        logger.info(f"Generating working capital forecast over {periods} periods")
        engine = self._get_engine(method)
        projected = engine.calculate(historical, periods, **kwargs)

        # Compute period-over-period absolute deltas
        deltas = []
        combined = historical + projected
        for i in range(len(historical), len(combined)):
            delta_val = combined[i] - combined[i - 1]
            deltas.append(delta_val)

        return WorkingCapitalForecast(
            historical=historical,
            projected=projected,
            method=method,
            confidence=confidence,
            delta=tuple(deltas),
        )

    def generate_scenario(
        self,
        scenario_name: str,
        probability: float,
        historical_revenue: Tuple[float, ...],
        historical_margin: Tuple[float, ...],
        historical_capex: Tuple[float, ...],
        periods: int,
        method: ForecastMethod = ForecastMethod.CAGR,
    ) -> ForecastScenario:
        """Orchestrates and bundles a complete financial scenario package."""
        logger.info(
            f"Assembling scenario: {scenario_name} (probability: {probability})"
        )

        rev_f = self.generate_revenue_forecast(
            historical_revenue, periods, method=method
        )
        margin_f = self.generate_margin_forecast(historical_margin, periods)
        capex_f = self.generate_capex_forecast(historical_capex, periods)
        tax_f = TaxForecast(historical=(0.25, 0.25), projected=(0.25, 0.25))
        tg_f = TerminalGrowthForecast(terminal_growth=0.03, method=method)

        return ForecastScenario(
            scenario_name=scenario_name,
            probability=probability,
            revenue_forecast=rev_f,
            margin_forecast=margin_f,
            capex_forecast=capex_f,
            tax_forecast=tax_f,
            terminal_growth=tg_f,
        )
