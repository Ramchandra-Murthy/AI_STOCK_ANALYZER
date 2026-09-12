from __future__ import annotations

import logging
from math import isfinite

from services.financials.financial_statement import FinancialStatements
from services.ratios.models import FinancialRatios

logger = logging.getLogger(__name__)


class FinancialRatioEngine:
    """Derive financial ratios from supplied normalized financial statements only."""

    @staticmethod
    def _calculate_cagr(start_value: float, end_value: float, periods: int) -> float:
        start = float(start_value)
        end = float(end_value)
        if periods <= 0 or start <= 0 or end <= 0:
            return 0.0
        if not isfinite(start) or not isfinite(end):
            return 0.0
        return round(((end / start) ** (1.0 / periods) - 1.0) * 100.0, 2)

    def compute_ratios(self, financials: FinancialStatements) -> FinancialRatios:
        if not isinstance(financials, FinancialStatements):
            raise TypeError("financials must be a FinancialStatements instance")
        if not isinstance(financials.symbol, str) or not financials.symbol.strip():
            raise ValueError("financials.symbol must be non-empty")

        incomes = financials.income_statements
        balances = financials.balance_sheets
        cashflows = financials.cash_flows
        if not incomes or not balances or not cashflows:
            raise ValueError(
                "financial statements must contain income, balance-sheet and cash-flow data"
            )

        inc = incomes[-1]
        bs = balances[-1]
        cf = cashflows[-1]
        period = inc.period

        revenue = float(inc.revenue)
        net_income = float(inc.net_income)
        ebit = float(inc.ebit)
        operating_income = float(inc.operating_income)
        total_assets = float(bs.total_assets)
        total_liab = float(bs.total_liabilities)
        equity = float(bs.shareholders_equity or bs.total_equity)
        cash = float(bs.total_cash)
        debt = float(bs.total_debt)
        op_cf = float(cf.operating_cash_flow)
        fcf = float(cf.free_cash_flow)
        capex = float(cf.capex or cf.capital_expenditure)

        if revenue <= 0 or total_assets <= 0 or equity <= 0:
            raise ValueError("revenue, total_assets and equity must be positive for ratio analysis")

        invested_capital = equity + debt - cash
        profitability = {
            "net_margin": round((net_income / revenue) * 100.0, 2),
            "operating_margin": round((operating_income / revenue) * 100.0, 2),
            "ebit_margin": round((ebit / revenue) * 100.0, 2),
            "roe": round((net_income / equity) * 100.0, 2),
            "roce": round((ebit / total_assets) * 100.0, 2),
            "roic": round((ebit / invested_capital) * 100.0, 2) if invested_capital > 0 else 0.0,
            "croic": round((op_cf / invested_capital) * 100.0, 2) if invested_capital > 0 else 0.0,
        }

        current_assets = float(bs.current_assets)
        current_liabilities = float(bs.current_liabilities)
        liquidity = {
            "current_ratio": (
                round(current_assets / current_liabilities, 2) if current_liabilities > 0 else 0.0
            ),
            "cash_ratio": round(cash / current_liabilities, 2) if current_liabilities > 0 else 0.0,
            "quick_ratio": (
                round((current_assets - float(bs.inventory)) / current_liabilities, 2)
                if current_liabilities > 0
                else 0.0
            ),
        }

        interest_expense = abs(float(inc.finance_cost))
        solvency = {
            "debt_to_equity": round(debt / equity, 2),
            "net_debt_to_equity": round((debt - cash) / equity, 2),
            "interest_coverage": round(ebit / interest_expense, 2) if interest_expense > 0 else 0.0,
            "debt_to_capital": round(debt / (equity + debt), 2) if equity + debt > 0 else 0.0,
        }

        efficiency = {
            "asset_turnover": round(revenue / total_assets, 2),
            "capital_turnover": (
                round(revenue / invested_capital, 2) if invested_capital > 0 else 0.0
            ),
        }

        growth = {"revenue_cagr_3y": 0.0, "net_income_cagr_3y": 0.0, "eps_cagr_3y": 0.0}
        if len(incomes) >= 3:
            periods = len(incomes) - 1
            growth = {
                "revenue_cagr_3y": self._calculate_cagr(incomes[0].revenue, inc.revenue, periods),
                "net_income_cagr_3y": self._calculate_cagr(
                    incomes[0].net_income, inc.net_income, periods
                ),
                "eps_cagr_3y": self._calculate_cagr(incomes[0].eps, inc.eps, periods),
            }

        cash_flow = {
            "fcf_margin": round((fcf / revenue) * 100.0, 2),
            "fcf_conversion": round((fcf / net_income) * 100.0, 2) if net_income != 0 else 0.0,
            "capex_to_revenue": round((abs(capex) / revenue) * 100.0, 2),
            "owner_earnings": round(op_cf - abs(capex), 2),
        }

        # Scores that require additional forensic datasets are explicitly marked
        # unavailable instead of being fabricated.
        quality_scores = {
            "piotroski_f_score": 0.0,
            "altman_z_score": 0.0,
            "beneish_m_score": 0.0,
            "accrual_ratio": round((net_income - op_cf) / total_assets, 4),
        }

        return FinancialRatios(
            symbol=financials.symbol.strip().upper(),
            period=period,
            profitability=profitability,
            liquidity=liquidity,
            solvency=solvency,
            efficiency=efficiency,
            growth=growth,
            cash_flow=cash_flow,
            quality_scores=quality_scores,
            metadata={"version": "6.4", "quality_score_status": "FORENSIC_INPUTS_REQUIRED"},
        )
