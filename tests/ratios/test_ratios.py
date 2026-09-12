from __future__ import annotations

from services.financials.balance_sheet import BalanceSheet
from services.financials.cash_flow import CashFlowStatement
from services.financials.financial_statement import FinancialStatements, PeriodFinancials
from services.financials.income_statement import IncomeStatement
from services.ratios.engine import FinancialRatioEngine


def test_financial_ratio_engine() -> None:
    engine = FinancialRatioEngine()

    income = IncomeStatement(
        period="2025",
        revenue=100000.0,
        total_operating_income=20000.0,
        ebit=18000.0,
        net_income=12000.0,
        eps=12.0,
    )

    balance = BalanceSheet(
        period="2025",
        total_assets=250000.0,
        total_liabilities=100000.0,
        total_equity=150000.0,
        cash=20000.0,
        long_term_debt=50000.0,
    )

    cashflow = CashFlowStatement(
        period="2025",
        operating_cash_flow=22000.0,
        capital_expenditure=5000.0,
        investing_cash_flow=-6000.0,
        financing_cash_flow=-8000.0,
    )

    fin = FinancialStatements(
        company_name="RELIANCE",
        ticker="RELIANCE.NS",
        currency="INR",
        fiscal_year="2025",
        income_statement=income,
        balance_sheet=balance,
        cash_flow_statement=cashflow,
        periods=[
            PeriodFinancials(
                period="2025",
                income_statement=income,
                balance_sheet=balance,
                cash_flow_statement=cashflow,
            )
        ],
    )

    ratios = engine.compute_ratios(fin)

    assert ratios.symbol == "RELIANCE.NS"
    assert ratios.profitability["net_margin"] > 0
    assert ratios.solvency["debt_to_equity"] > 0
    assert ratios.quality_scores["piotroski_f_score"] == 8.0
