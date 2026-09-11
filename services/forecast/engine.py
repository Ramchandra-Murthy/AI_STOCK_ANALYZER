from __future__ import annotations

import logging

from services.financials.financial_statement import FinancialStatements
from services.forecast.cagr import CAGRCalculator
from services.forecast.growth import ExponentialForecaster
from services.forecast.models import ForecastResult
from services.forecast.regression import RegressionForecaster

logger = logging.getLogger(__name__)


class ForecastEngine:
    """Institutional forecast engine using validated historical financials only."""

    def __init__(self) -> None:
        self.cagr_calc = CAGRCalculator()
        self.regression_calc = RegressionForecaster()
        self.exponential_calc = ExponentialForecaster()

    def generate_forecast(
        self,
        financials: FinancialStatements,
        model_type: str = "CAGR",
    ) -> ForecastResult:
        symbol = financials.symbol.strip() if isinstance(financials.symbol, str) else ""
        if not symbol:
            raise ValueError("financials.symbol must be non-empty")

        income_history = sorted(financials.income_statements, key=lambda item: item.period)
        cashflow_history = sorted(financials.cash_flows, key=lambda item: item.period)
        if len(income_history) < 2:
            raise ValueError("at least two income-statement periods are required")
        if len(cashflow_history) < 2:
            raise ValueError("at least two cash-flow periods are required")

        revenues = [float(inc.revenue) for inc in income_history]
        ebits = [float(inc.ebit) for inc in income_history]
        eps_list = [float(inc.eps) for inc in income_history]
        fcf_list = [float(cf.free_cash_flow) for cf in cashflow_history]

        model = model_type.strip().upper() if isinstance(model_type, str) else ""
        if model == "LINEAR_REGRESSION":
            rev_proj = self.regression_calc.project(revenues, periods=5)
            ebit_proj = self.regression_calc.project(ebits, periods=5)
            eps_proj = self.regression_calc.project(eps_list, periods=5)
            fcf_proj = self.regression_calc.project(fcf_list, periods=5)
        elif model == "EXPONENTIAL":
            # Growth is estimated from actual history by the forecaster; no
            # fixed company-level growth assumptions are used as data.
            rev_proj = self.exponential_calc.project(revenues, periods=5)
            ebit_proj = self.exponential_calc.project(ebits, periods=5)
            eps_proj = self.exponential_calc.project(eps_list, periods=5)
            fcf_proj = self.exponential_calc.project(fcf_list, periods=5)
        elif model == "CAGR":
            cagr = self.cagr_calc.calculate_cagr(
                revenues[0], revenues[-1], max(1, len(revenues) - 1)
            )
            rev_proj = self.cagr_calc.project(revenues[-1], cagr, periods=5)
            ebit_proj = self.cagr_calc.project(ebits[-1], cagr * 0.9, periods=5)
            eps_proj = self.cagr_calc.project(eps_list[-1], cagr * 0.95, periods=5)
            fcf_proj = self.cagr_calc.project(fcf_list[-1], cagr, periods=5)
        else:
            raise ValueError(
                "model_type must be one of: CAGR, LINEAR_REGRESSION, EXPONENTIAL"
            )

        capex_proj = [revenue * 0.08 for revenue in rev_proj]
        wc_proj = [revenue * 0.05 for revenue in rev_proj]
        dep_proj = [ebit * 0.3 for ebit in ebit_proj]

        logger.info("Generated %s forecast for %s from actual financial history", model, symbol)
        return ForecastResult(
            symbol=symbol,
            model_type=model,
            forecast_periods=5,
            revenue_forecast=rev_proj,
            ebit_forecast=ebit_proj,
            eps_forecast=eps_proj,
            free_cash_flow_forecast=fcf_proj,
            capex_forecast=capex_proj,
            working_capital_forecast=wc_proj,
            depreciation_forecast=dep_proj,
            assumptions={"base_revenue": revenues[-1], "model": model},
        )
