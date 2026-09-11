from __future__ import annotations

import logging
from math import isfinite

from services.financials.financial_statement import FinancialStatements
from services.forecast.cagr import CAGRCalculator
from services.forecast.growth import ExponentialForecaster
from services.forecast.models import ForecastResult
from services.forecast.regression import RegressionForecaster

logger = logging.getLogger(__name__)


class ForecastEngine:
    """Forecast validated historical financial series without fabricated data."""

    PERIODS = 5

    def __init__(self) -> None:
        self.cagr_calc = CAGRCalculator()
        self.regression_calc = RegressionForecaster()
        self.exponential_calc = ExponentialForecaster()

    def generate_forecast(
        self,
        financials: FinancialStatements,
        model_type: str = "CAGR",
    ) -> ForecastResult:
        if not isinstance(financials, FinancialStatements):
            raise TypeError("financials must be a FinancialStatements instance")
        symbol = financials.symbol.strip().upper() if isinstance(financials.symbol, str) else ""
        if not symbol:
            raise ValueError("financials.symbol must be non-empty")

        income_history = sorted(financials.income_statements, key=lambda item: item.period)
        cashflow_history = sorted(financials.cash_flows, key=lambda item: item.period)
        if len(income_history) < 2 or len(cashflow_history) < 2:
            raise ValueError("at least two periods of income and cash-flow history are required")

        revenues = self._positive_series("revenue", [item.revenue for item in income_history])
        ebits = self._finite_series("ebit", [item.ebit for item in income_history])
        eps_list = self._finite_series("eps", [item.eps for item in income_history])
        fcf_list = self._finite_series("free_cash_flow", [item.free_cash_flow for item in cashflow_history])
        capex_history = self._finite_series(
            "capex", [abs(item.capex or item.capital_expenditure) for item in cashflow_history]
        )
        working_capital_history = self._finite_series(
            "working_capital",
            [item.change_in_working_capital for item in cashflow_history],
        )
        depreciation_history = self._finite_series(
            "depreciation",
            [item.depreciation_and_amortization for item in income_history],
        )

        model = model_type.strip().upper() if isinstance(model_type, str) else ""
        if model == "CAGR":
            rev_proj = self._cagr_project(revenues)
            ebit_proj = self._cagr_project_signed(ebits)
            eps_proj = self._cagr_project_signed(eps_list)
            fcf_proj = self._cagr_project_signed(fcf_list)
            capex_proj = self._cagr_project_signed(capex_history)
            wc_proj = self._cagr_project_signed(working_capital_history)
            dep_proj = self._cagr_project_signed(depreciation_history)
        elif model == "LINEAR_REGRESSION":
            rev_proj = self.regression_calc.project(revenues, periods=self.PERIODS)
            ebit_proj = self.regression_calc.project(ebits, periods=self.PERIODS)
            eps_proj = self.regression_calc.project(eps_list, periods=self.PERIODS)
            fcf_proj = self.regression_calc.project(fcf_list, periods=self.PERIODS)
            capex_proj = self.regression_calc.project(capex_history, periods=self.PERIODS)
            wc_proj = self.regression_calc.project(working_capital_history, periods=self.PERIODS)
            dep_proj = self.regression_calc.project(depreciation_history, periods=self.PERIODS)
        elif model == "EXPONENTIAL":
            rev_proj = self.exponential_calc.project(revenues, periods=self.PERIODS)
            ebit_proj = self._exponential_signed(ebits)
            eps_proj = self._exponential_signed(eps_list)
            fcf_proj = self._exponential_signed(fcf_list)
            capex_proj = self._exponential_signed(capex_history)
            wc_proj = self._exponential_signed(working_capital_history)
            dep_proj = self._exponential_signed(depreciation_history)
        else:
            raise ValueError("model_type must be one of: CAGR, LINEAR_REGRESSION, EXPONENTIAL")

        return ForecastResult(
            symbol=symbol,
            model_type=model,
            forecast_periods=self.PERIODS,
            revenue_forecast=rev_proj,
            ebit_forecast=ebit_proj,
            eps_forecast=eps_proj,
            free_cash_flow_forecast=fcf_proj,
            capex_forecast=capex_proj,
            working_capital_forecast=wc_proj,
            depreciation_forecast=dep_proj,
            assumptions={
                "history_periods": len(income_history),
                "model": model,
                "forecast_basis": "historical_financial_statements",
            },
        )

    def _cagr_project(self, values: list[float]) -> list[float]:
        if any(value <= 0 for value in values):
            raise ValueError("CAGR requires strictly positive history")
        rate = self.cagr_calc.calculate_cagr(values[0], values[-1], len(values) - 1)
        return self.cagr_calc.project(values[-1], rate, periods=self.PERIODS)

    def _cagr_project_signed(self, values: list[float]) -> list[float]:
        if all(value > 0 for value in values):
            return self._cagr_project(values)
        if all(value < 0 for value in values):
            projected = self._cagr_project([-value for value in values])
            return [-value for value in projected]
        return self.regression_calc.project(values, periods=self.PERIODS)

    def _exponential_signed(self, values: list[float]) -> list[float]:
        if all(value > 0 for value in values):
            return self.exponential_calc.project(values, periods=self.PERIODS)
        if all(value < 0 for value in values):
            projected = self.exponential_calc.project([-value for value in values], periods=self.PERIODS)
            return [-value for value in projected]
        return self.regression_calc.project(values, periods=self.PERIODS)

    @staticmethod
    def _finite_series(name: str, values: list[float]) -> list[float]:
        result = [float(value) for value in values]
        if not result or any(not isfinite(value) for value in result):
            raise ValueError(f"{name} history must contain finite numeric values")
        return result

    @staticmethod
    def _positive_series(name: str, values: list[float]) -> list[float]:
        result = ForecastEngine._finite_series(name, values)
        if any(value <= 0 for value in result):
            raise ValueError(f"{name} history must contain positive values")
        return result
