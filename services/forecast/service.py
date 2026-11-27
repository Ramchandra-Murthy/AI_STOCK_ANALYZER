from __future__ import annotations

import logging
import time
from math import isfinite

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
    ForecastAssumption,
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
            derived = AssumptionEngine.derive_from_financials(
                AssumptionDerivationInput(
                    historical_revenue=forecast_input.historical_revenue,
                    historical_margins=forecast_input.historical_margins,
                    historical_capex=forecast_input.historical_capex,
                    historical_nwc=forecast_input.historical_working_capital,
                    historical_tax_rates=forecast_input.historical_taxes,
                    explicit_tax_rate_fallback=forecast_input.tax_rate_assumption,
                    historical_years=forecast_input.historical_years,
                    management_guidance=forecast_input.management_guidance,
                    working_capital_pct_revenue_fallback=(
                        forecast_input.working_capital_pct_revenue_assumption
                    ),
                    ebit_margin_fallback=(
                        float(forecast_input.management_guidance.target_ebit_margin_override)
                        if forecast_input.management_guidance is not None
                        and forecast_input.management_guidance.target_ebit_margin_override
                        is not None
                        else forecast_input.ebit_margin_assumption
                    ),
                    capex_pct_revenue_fallback=forecast_input.capex_pct_revenue_assumption,
                )
            )

            guidance = forecast_input.management_guidance
            guidance_growth = getattr(guidance, "revenue_cagr_override", None)
            guidance_margin = getattr(guidance, "target_ebit_margin_override", None)
            explicit_growth = (
                guidance_growth
                if guidance_growth is not None
                else forecast_input.custom_growth_rate
            )
            if explicit_growth is not None:
                algorithm_growth = float(explicit_growth)
                growth_method = (
                    "management_override"
                    if guidance_growth is not None
                    else "explicit_input"
                )
            elif isinstance(self.algorithm, LinearRegressionForecastEngine):
                history = forecast_input.historical_revenue
                n = len(history)
                mean_x = (n - 1) / 2.0
                mean_y = sum(history) / n
                denominator = sum((i - mean_x) ** 2 for i in range(n))
                slope = (
                    sum((i - mean_x) * (value - mean_y) for i, value in enumerate(history))
                    / denominator
                    if denominator
                    else 0.0
                )
                algorithm_growth = slope / history[-1]
                if not isfinite(algorithm_growth) or algorithm_growth <= -1.0:
                    raise ForecastConfigurationError(
                        "Linear-regression revenue growth must be finite and greater than -100%."
                    )
                growth_method = "linear_regression_slope_over_latest_revenue"
            else:
                algorithm_growth = derived.revenue_growth_rate
                growth_method = "historical_geometric_cagr"

            growth = float(algorithm_growth)
            ebit_margin = (
                float(guidance_margin)
                if guidance_margin is not None
                else (
                    float(forecast_input.ebit_margin_assumption)
                    if forecast_input.ebit_margin_assumption is not None
                    else float(derived.ebitda_margin)
                )
            )
            capex_ratio = (
                float(forecast_input.capex_pct_revenue_assumption)
                if forecast_input.capex_pct_revenue_assumption is not None
                else float(derived.capex_pct_revenue)
            )
            nwc_ratio = (
                float(forecast_input.working_capital_pct_revenue_assumption)
                if forecast_input.working_capital_pct_revenue_assumption is not None
                else float(derived.working_capital_pct_revenue)
            )
            tax_rate = float(derived.tax_rate)

            provenance = {
                "revenue_growth": {
                    "method": (
                        "management_override"
                        if guidance_growth is not None
                        else (
                            "explicit_input"
                            if forecast_input.custom_growth_rate is not None
                            else growth_method
                        )
                    ),
                    "value": growth,
                },
                "ebit_margin": {
                    "method": (
                        "management_override"
                        if guidance_margin is not None
                        else (
                            "explicit_input"
                            if forecast_input.ebit_margin_assumption is not None
                            else "historical_ebit_margin"
                        )
                    ),
                    "value": ebit_margin,
                    "legacy_model_field": "ebitda_margin",
                },
                "capex_pct_revenue": {
                    "method": (
                        "explicit_input"
                        if forecast_input.capex_pct_revenue_assumption is not None
                        else "historical_abs_capex_to_revenue"
                    ),
                    "value": capex_ratio,
                },
                "working_capital_pct_revenue": {
                    "method": (
                        "explicit_input"
                        if forecast_input.working_capital_pct_revenue_assumption is not None
                        else "historical_nwc_to_revenue"
                    ),
                    "value": nwc_ratio,
                },
                "tax_rate": dict(derived.metadata["tax"]),
            }
            assumptions = ForecastAssumption(
                revenue_growth_rate=growth,
                ebitda_margin=ebit_margin,
                tax_rate=tax_rate,
                capex_pct_revenue=capex_ratio,
                working_capital_pct_revenue=nwc_ratio,
                metadata={
                    **derived.metadata,
                    "engine_version": "f10a-6",
                    "margin_semantics": (
                        "EBIT margin; ebitda_margin retained as a legacy serialized field"
                    ),
                    "provenance": provenance,
                    "management_guidance": (
                        {"source": guidance.source, "reason": guidance.reason}
                        if guidance is not None
                        and (guidance_growth is not None or guidance_margin is not None)
                        else None
                    ),
                },
            )

            revenues: list[float] = []
            last_revenue = float(forecast_input.historical_revenue[-1])
            for _ in years:
                last_revenue *= 1.0 + growth
                revenues.append(last_revenue)
            revenue_values = tuple(revenues)
            margins = tuple(ebit_margin for _ in years)
            ebit = tuple(
                revenue * margin for revenue, margin in zip(revenue_values, margins, strict=True)
            )
            # CapEx is represented as a positive expenditure magnitude. Downstream
            # cash-flow calculations apply the cash-outflow sign.
            capex = tuple(revenue * capex_ratio for revenue in revenue_values)
            depreciation = self.algorithm.calculate_depreciation(forecast_input)
            working_capital = tuple(revenue * nwc_ratio for revenue in revenue_values)
            taxes = tuple(tax_rate for _ in years)

            package = ForecastPackage(
                ticker=forecast_input.ticker,
                years=years,
                revenue=ForecastLineItem("Revenue", revenue_values),
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
                    "assumption_engine": assumptions.metadata,
                    "assumptions": assumptions.to_dict(),
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
                    working_capital_pct_revenue_fallback=(working_capital_pct_revenue_assumption),
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
