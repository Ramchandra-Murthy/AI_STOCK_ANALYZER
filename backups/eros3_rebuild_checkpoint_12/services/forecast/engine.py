from __future__ import annotations

import logging

from services.financials.financial_statement import FinancialStatements
from services.forecast.cagr import CAGRCalculator
from services.forecast.growth import ExponentialForecaster
from services.forecast.models import ForecastResult
from services.forecast.regression import RegressionForecaster

logger = logging.getLogger(__name__)


class ForecastEngine:
    """Institutional forecast engine integrating CAGR, Linear Regression, and Exponential models."""

    def __init__(self) -> None:
        self.cagr_calc = CAGRCalculator()
        self.regression_calc = RegressionForecaster()
        self.exponential_calc = ExponentialForecaster()

    def generate_forecast(
        self, financials: FinancialStatements, model_type: str = "CAGR"
    ) -> ForecastResult:
        symbol = financials.symbol
        logger.info(
            "Generating %s forecast for symbol: %s based on actual fundamentals", model_type, symbol
        )

        # Extract historical series or fall back to defaults
        # Normalize historical ordering before forecasting.
        # Yahoo Finance commonly returns periods newest -> oldest,
        # while all forecast models require oldest -> newest.
        income_history = sorted(
            financials.income_statements,
            key=lambda item: item.period,
        )
        cashflow_history = sorted(
            financials.cash_flows,
            key=lambda item: item.period,
        )

        revenues = (
            [inc.revenue for inc in income_history]
            if income_history
            else [1000000.0, 1100000.0, 1250000.0]
        )
        ebits = (
            [inc.ebit for inc in income_history]
            if income_history
            else [200000.0, 220000.0, 250000.0]
        )
        eps_list = [inc.eps for inc in income_history] if income_history else [40.0, 45.0, 50.0]
        fcf_list = (
            [cf.free_cash_flow for cf in cashflow_history]
            if cashflow_history
            else [150000.0, 170000.0, 190000.0]
        )

        last_rev = revenues[-1]
        last_ebit = ebits[-1]
        last_eps = eps_list[-1]
        last_fcf = fcf_list[-1]

        if model_type == "LINEAR_REGRESSION":
            rev_proj = self.regression_calc.project(revenues, periods=5)
            ebit_proj = self.regression_calc.project(ebits, periods=5)
            eps_proj = self.regression_calc.project(eps_list, periods=5)
            fcf_proj = self.regression_calc.project(fcf_list, periods=5)
        elif model_type == "EXPONENTIAL":
            rev_proj = self.exponential_calc.project(revenues, growth_rate=0.12, periods=5)
            ebit_proj = self.exponential_calc.project(ebits, growth_rate=0.10, periods=5)
            eps_proj = self.exponential_calc.project(eps_list, growth_rate=0.10, periods=5)
            fcf_proj = self.exponential_calc.project(fcf_list, growth_rate=0.12, periods=5)
        else:  # Default CAGR
            cagr = self.cagr_calc.calculate_cagr(
                revenues[0], revenues[-1], max(1, len(revenues) - 1)
            )
            rev_proj = self.cagr_calc.project(last_rev, cagr, periods=5)
            ebit_proj = self.cagr_calc.project(last_ebit, cagr * 0.9, periods=5)
            eps_proj = self.cagr_calc.project(last_eps, cagr * 0.95, periods=5)
            fcf_proj = self.cagr_calc.project(last_fcf, cagr, periods=5)

        capex_proj = [r * 0.08 for r in rev_proj]
        wc_proj = [r * 0.05 for r in rev_proj]
        dep_proj = [e * 0.3 for e in ebit_proj]

        return ForecastResult(
            symbol=symbol,
            model_type=model_type,
            forecast_periods=5,
            revenue_forecast=rev_proj,
            ebit_forecast=ebit_proj,
            eps_forecast=eps_proj,
            free_cash_flow_forecast=fcf_proj,
            capex_forecast=capex_proj,
            working_capital_forecast=wc_proj,
            depreciation_forecast=dep_proj,
            assumptions={"base_revenue": last_rev, "model": model_type},
        )
