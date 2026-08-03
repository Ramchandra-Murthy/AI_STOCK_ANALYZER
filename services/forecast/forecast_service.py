"""
==========================================================
EQUITY VALUATION PLATFORM v5.1
Module  : services.forecast.forecast_service
Layer   : Services / Forecast / Orchestration Service
Summary : Top-level facade coordinating subservices for comprehensive
          financial forecasting.
==========================================================
"""

from __future__ import annotations

from typing import Any, Callable, Optional, Tuple

from core.logger import logger
from services.forecast.capex_forecast import CapexForecastEngine
from services.forecast.confidence_engine import ForecastConfidenceCalculator
from services.forecast.depreciation_forecast import DepreciationForecastEngine
from services.forecast.forecast_input import ForecastInput
from services.forecast.forecast_models import (
    ForecastMethod,
    ValuationError,
)
from services.forecast.forecast_result import ForecastResult
from services.forecast.margin_forecast import MarginForecastEngine
from services.forecast.revenue_forecast import RevenueForecastEngine
from services.forecast.tax_forecast import TaxForecastEngine
from services.forecast.terminal_growth import TerminalGrowthEngine
from services.forecast.validation import ForecastDataValidator
from services.forecast.working_capital_forecast import WorkingCapitalForecastEngine


def _invoke_subservice(
    func: Callable[..., Any],
    inp: ForecastInput,
    method: Optional[ForecastMethod] = None,
    *extra_args: Any,
) -> Any:
    """Helper to cleanly route execution to subservices with complete ForecastInput contracts."""
    try:
        return func(inp, *extra_args, method=method)
    except TypeError:
        return func(inp, *extra_args)


class ForecastService:
    """Master orchestrator for financial forecasts."""

    def __init__(self) -> None:
        self.validator = ForecastDataValidator()
        self.revenue_engine = RevenueForecastEngine()
        self.margin_engine = MarginForecastEngine()
        self.capex_engine = CapexForecastEngine()
        self.depreciation_engine = DepreciationForecastEngine()
        self.working_capital_engine = WorkingCapitalForecastEngine()
        self.tax_engine = TaxForecastEngine()
        self.terminal_growth_engine = TerminalGrowthEngine()
        self.confidence_calculator = ForecastConfidenceCalculator()

    def generate_forecast(
        self,
        inp: ForecastInput,
        method: Optional[ForecastMethod] = None,
    ) -> ForecastResult:
        """Runs pre-flight validation and dispatches execution across all line-item engines."""
        logger.info(
            f"[FORECAST SERVICE] Generating institutional forecast suite for symbol: {inp.symbol}"
        )

        # 1. Audit input data quality
        report = self.validator.validate_input(inp)
        if not report.is_valid:
            raise ValuationError(
                f"ForecastInput failed validation: {', '.join(report.errors)}"
            )

        # 2. Execute Subservices
        rev_forecast = _invoke_subservice(
            self.revenue_engine.forecast_revenue, inp, method
        )
        margin_forecast = _invoke_subservice(
            self.margin_engine.forecast_margins, inp, method
        )
        capex_forecast = _invoke_subservice(
            self.capex_engine.forecast_capex, inp, method, rev_forecast.projected
        )
        dep_forecast = _invoke_subservice(
            self.depreciation_engine.forecast_depreciation,
            inp,
            method,
            rev_forecast.projected,
        )
        nwc_forecast = _invoke_subservice(
            self.working_capital_engine.forecast_working_capital,
            inp,
            method,
            rev_forecast.projected,
        )
        tax_forecast = _invoke_subservice(self.tax_engine.forecast_tax, inp, method)
        terminal_growth = self.terminal_growth_engine.forecast_terminal_growth(inp)

        # 3. Calculate Confidence Metric
        confidence = self.confidence_calculator.evaluate(
            inp=inp,
            revenue=rev_forecast,
            margin=margin_forecast,
            validation_report=report,
        )

        # 4. Construct Output Result Container
        return ForecastResult(
            symbol=inp.symbol,
            revenue=rev_forecast,
            margin=margin_forecast,
            capex=capex_forecast,
            depreciation=dep_forecast,
            working_capital=nwc_forecast,
            tax=tax_forecast,
            terminal_growth=terminal_growth,
            confidence=confidence,
        )

    def build_forecast(
        self,
        historical_revenues: Tuple[float, ...] | list[float],
        historical_ebits: Tuple[float, ...] | list[float],
        historical_nwc: Tuple[float, ...] | list[float],
        historical_capex: Tuple[float, ...] | list[float],
        forecast_years: int = 5,
        symbol: str = "GENERIC",
        method: ForecastMethod = ForecastMethod.CAGR,
    ) -> ForecastResult:
        """Legacy helper endpoint for direct parameter invocation."""
        inp = ForecastInput(
            symbol=symbol,
            historical_revenues=tuple(historical_revenues),
            historical_ebits=tuple(historical_ebits),
            historical_nwc=tuple(historical_nwc),
            historical_capex=tuple(historical_capex),
            forecast_years=forecast_years,
            method=method,
        )
        return self.generate_forecast(inp)
