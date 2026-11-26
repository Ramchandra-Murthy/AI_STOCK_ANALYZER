from __future__ import annotations

import logging
import time

from services.forecast.algorithms.base import BaseForecastAlgorithm
from services.forecast.algorithms.cagr import CAGRForecastEngine
from services.forecast.algorithms.linear_regression import LinearRegressionForecastEngine
from services.forecast.assumption_engine import (
    AssumptionDerivationInput,
    AssumptionEngine,
)
from services.forecast.exceptions import ForecastConfigurationError, ForecastError
from services.forecast.input import ForecastInput
from services.forecast.models import (
    CapexForecast,
    ConfidenceLevel,
    DepreciationForecast,
    ForecastConfidence,
    ForecastLineItem,
    ForecastMethod,
    ForecastPackage,
    ForecastScenario,
    MarginForecast,
    RevenueForecast,
    TaxForecast,
    TerminalGrowthForecast,
    WorkingCapitalForecast,
)
from services.forecast.result import ForecastResult
from services.forecast.validation import ForecastValidator

logger = logging.getLogger(__name__)


class ForecastService:
    def __init__(self, algorithm: BaseForecastAlgorithm | None = None) -> None:
        self.algorithm = algorithm or CAGRForecastEngine()

    def execute(self, forecast_input: ForecastInput) -> ForecastResult:
        start_time = time.perf_counter()
        try:
            ForecastValidator.validate_input(forecast_input)
            years = forecast_input.forecast_years
            revenues = self.algorithm.calculate_revenue(forecast_input)
            margins = self.algorithm.calculate_margins(forecast_input)
            capex = self.algorithm.calculate_capex(forecast_input)
            depreciation = self.algorithm.calculate_depreciation(forecast_input)
            derived_assumptions = AssumptionEngine.derive_from_financials(
                AssumptionDerivationInput(
                    historical_revenue=forecast_input.historical_revenue,
                    historical_margins=forecast_input.historical_margins,
                    historical_capex=forecast_input.historical_capex,
                    historical_nwc=forecast_input.historical_working_capital,
                    historical_tax_rates=forecast_input.historical_taxes,
                    explicit_tax_rate_fallback=forecast_input.tax_rate_assumption,
                    historical_years=forecast_input.historical_years,
                )
            )
            working_capital = tuple(
                revenue * derived_assumptions.working_capital_pct_revenue for revenue in revenues
            )
            taxes = tuple(derived_assumptions.tax_rate for _ in forecast_input.forecast_years)
            ebit = tuple(r * m for r, m in zip(revenues, margins, strict=False))
            package = ForecastPackage(
                ticker=forecast_input.ticker,
                years=years,
                revenue=ForecastLineItem("Revenue", revenues),
                ebit=ForecastLineItem("EBIT", ebit),
                capex=ForecastLineItem("Capital Expenditures", capex),
                depreciation=ForecastLineItem("Depreciation", depreciation),
                working_capital=ForecastLineItem("Working Capital", working_capital),
                tax_rate=ForecastLineItem("Tax Rate", taxes),
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ForecastResult(
                package=package,
                execution_time_ms=round(elapsed_ms, 3),
                status="SUCCESS",
                metadata={
                    "algorithm": self.algorithm.__class__.__name__,
                    "assumption_engine": derived_assumptions.metadata,
                },
            )
        except (ForecastError, ValueError) as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            empty_item = ForecastLineItem("", ())
            pkg = ForecastPackage(
                ticker=forecast_input.ticker,
                years=(),
                revenue=empty_item,
                ebit=empty_item,
                capex=empty_item,
                depreciation=empty_item,
                working_capital=empty_item,
                tax_rate=empty_item,
            )
            return ForecastResult(
                package=pkg,
                execution_time_ms=round(elapsed_ms, 3),
                status="FAILED",
                error_message=str(e),
                metadata={"algorithm": self.algorithm.__class__.__name__},
            )

    def generate_revenue_forecast(
        self,
        historical: tuple[float, ...],
        periods: int,
        method: ForecastMethod = ForecastMethod.CAGR,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    ) -> RevenueForecast:
        algorithm = self._algorithm_for(method)
        projected = algorithm.calculate(historical, periods)
        growth_rates = tuple(
            ((projected[i] / historical[-1]) - 1.0) if historical and historical[-1] != 0 else 0.0
            for i in range(len(projected))
        )
        return RevenueForecast(
            historical=historical,
            projected=projected,
            method=method,
            confidence=confidence,
            growth_rates=growth_rates,
        )

    def generate_working_capital_forecast(
        self,
        historical: tuple[float, ...],
        periods: int,
        method: ForecastMethod = ForecastMethod.CAGR,
        confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
    ) -> WorkingCapitalForecast:
        algorithm = self._algorithm_for(method)
        projected = algorithm.calculate(historical, periods)
        return WorkingCapitalForecast(
            historical=historical,
            projected=projected,
            method=method,
            confidence=confidence,
        )

    def generate_scenario(
        self,
        scenario_name: str,
        probability: float,
        historical_revenue: tuple[float, ...],
        historical_margin: tuple[float, ...],
        historical_capex: tuple[float, ...],
        periods: int,
        method: ForecastMethod = ForecastMethod.CAGR,
        *,
        historical_working_capital: tuple[float, ...] = (),
        historical_tax_rates: tuple[float, ...] = (),
        tax_rate_assumption: float | None = None,
        working_capital_pct_revenue_assumption: float | None = None,
    ) -> ForecastScenario:
        confidence = ConfidenceLevel.MEDIUM
        revenue = self.generate_revenue_forecast(historical_revenue, periods, method, confidence)
        margin_algorithm = self._algorithm_for(method)
        margins = tuple(
            max(0.0, min(1.0, value))
            for value in margin_algorithm.calculate(historical_margin, periods)
        )
        capex = CapexForecast(
            historical=historical_capex,
            projected=self._algorithm_for(method).calculate(historical_capex, periods),
            method=method,
            confidence=confidence,
        )
        if (
            not historical_working_capital
            and not historical_tax_rates
            and tax_rate_assumption is None
            and working_capital_pct_revenue_assumption is None
        ):
            # Explicit compatibility contract: only a call with none of the
            # F-10A working-capital or tax inputs uses pre-F-10A defaults.
            # Any partially configured call enters validated derivation and
            # must provide an independent source for each missing assumption.
            logger.warning(
                "generate_scenario is using deprecated legacy assumption defaults; "
                "provide historical_working_capital or "
                "working_capital_pct_revenue_assumption, and historical_tax_rates "
                "or tax_rate_assumption to use F-10A derivation"
            )
            assumptions = AssumptionEngine.derive_assumptions(
                historical_revenue, historical_margin, historical_capex, method
            )
            tax_history: tuple[float, ...] = ()
        else:
            assumptions = AssumptionEngine.derive_from_financials(
                AssumptionDerivationInput(
                    historical_revenue=historical_revenue,
                    historical_margins=historical_margin,
                    historical_capex=historical_capex,
                    historical_nwc=historical_working_capital,
                    historical_tax_rates=historical_tax_rates,
                    explicit_tax_rate_fallback=tax_rate_assumption,
                    working_capital_pct_revenue_fallback=(
                        working_capital_pct_revenue_assumption
                    ),
                )
            )
            tax_history = historical_tax_rates
        tax_projected = tuple(assumptions.tax_rate for _ in range(periods))
        taxes = TaxForecast(
            historical=tax_history,
            projected=tax_projected,
            method=method,
            confidence=confidence,
        )
        projected_working_capital = tuple(
            value * assumptions.working_capital_pct_revenue for value in revenue.projected
        )
        return ForecastScenario(
            scenario_name=scenario_name,
            method=method,
            probability=probability,
            revenue=revenue,
            margins=MarginForecast(
                historical=historical_margin,
                projected=margins,
                method=method,
                confidence=confidence,
            ),
            capex=capex,
            depreciation=DepreciationForecast(projected=(), method=method, confidence=confidence),
            working_capital=WorkingCapitalForecast(
                historical=historical_working_capital,
                projected=projected_working_capital,
                method=method,
                confidence=confidence,
            ),
            taxes=taxes,
            terminal_growth=TerminalGrowthForecast(0.03, ConfidenceLevel.HIGH),
            confidence=ForecastConfidence(85.0, ConfidenceLevel.HIGH),
            assumptions=assumptions,
        )

    @staticmethod
    def _algorithm_for(method: ForecastMethod) -> BaseForecastAlgorithm:
        """Return an implemented algorithm or reject an unsupported method.

        The canonical service currently supports CAGR and linear regression.
        Other enum members are retained for compatibility with other forecast
        layers, but must not silently produce a CAGR projection.
        """
        if method == ForecastMethod.CAGR:
            return CAGRForecastEngine()
        if method == ForecastMethod.LINEAR_REGRESSION:
            return LinearRegressionForecastEngine()
        raise ForecastConfigurationError(
            f"Forecast method '{method}' is not supported by the canonical "
            "forecast service. Supported methods: CAGR, LINEAR_REGRESSION."
        )
