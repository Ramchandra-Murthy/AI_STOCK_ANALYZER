from __future__ import annotations

import time

from services.forecast.algorithms.base import BaseForecastAlgorithm
from services.forecast.exceptions import ForecastError
from services.forecast.input import ForecastInput
from services.forecast.models import ForecastLineItem, ForecastPackage
from services.forecast.result import ForecastResult
from services.forecast.validation import ForecastValidator


class ForecastService:
    def __init__(self, algorithm: BaseForecastAlgorithm) -> None:
        self.algorithm = algorithm

    def execute(self, forecast_input: ForecastInput) -> ForecastResult:
        start_time = time.perf_counter()
        try:
            ForecastValidator.validate_input(forecast_input)
            years = forecast_input.forecast_years
            revenues = self.algorithm.calculate_revenue(forecast_input)
            margins = self.algorithm.calculate_margins(forecast_input)
            capex = self.algorithm.calculate_capex(forecast_input)
            depreciation = self.algorithm.calculate_depreciation(forecast_input)
            working_capital = self.algorithm.calculate_working_capital(forecast_input)
            taxes = self.algorithm.calculate_taxes(forecast_input)
            net_income = tuple(r * m for r, m in zip(revenues, margins, strict=False))
            package = ForecastPackage(
                ticker=forecast_input.ticker,
                years=years,
                revenue=ForecastLineItem("Revenue", revenues),
                net_income=ForecastLineItem("Net Income", net_income),
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
                metadata={"algorithm": self.algorithm.__class__.__name__},
            )
        except ForecastError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            empty_item = ForecastLineItem("", ())
            pkg = ForecastPackage(
                ticker=forecast_input.ticker,
                years=(),
                revenue=empty_item,
                net_income=empty_item,
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
