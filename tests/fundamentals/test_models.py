from __future__ import annotations

import pytest

from services.financials.financial_statement import FinancialStatements, PeriodFinancials
from services.financials.income_statement import IncomeStatement
from services.financials.balance_sheet import BalanceSheet
from services.financials.cash_flow import CashFlowStatement


def test_financial_statements_immutability_and_structure() -> None:
    inc = IncomeStatement(
        period="FY2025",
        revenue=100.0,
        total_operating_income=20.0,
        ebit=18.0,
        net_income=10.0,
        eps=2.0,
    )

    bs = BalanceSheet(
        period="FY2025",
        total_assets=500.0,
        total_liabilities=200.0,
        total_equity=300.0,
        cash=50.0,
        long_term_debt=100.0,
    )

    cf = CashFlowStatement(
        period="FY2025",
        operating_cash_flow=30.0,
        capital_expenditure=10.0,
        investing_cash_flow=-10.0,
        financing_cash_flow=-5.0,
    )

    fs = FinancialStatements(
        company_name="RELIANCE",
        ticker="RELIANCE.NS",
        currency="INR",
        fiscal_year="FY2025",
        income_statement=inc,
        balance_sheet=bs,
        cash_flow_statement=cf,
        periods=[
            PeriodFinancials(
                period="FY2025",
                income_statement=inc,
                balance_sheet=bs,
                cash_flow_statement=cf,
            )
        ],
    )

    assert fs.symbol == "RELIANCE.NS"
    assert fs.ticker == "RELIANCE.NS"

    assert len(fs.income_statements) == 1
    assert fs.income_statements[0].revenue == 100.0

    assert len(fs.balance_sheets) == 1
    assert fs.balance_sheets[0].shareholders_equity == 300.0

    assert len(fs.cash_flows) == 1
    assert fs.cash_flows[0].free_cash_flow == 20.0

    with pytest.raises(AttributeError):
        fs.symbol = "TCS.NS"  # type: ignore[misc]
