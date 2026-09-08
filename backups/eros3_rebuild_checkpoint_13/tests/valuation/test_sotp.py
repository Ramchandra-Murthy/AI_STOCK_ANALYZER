from __future__ import annotations

from services.financials.financial_statement import FinancialStatements
from services.financials.income_statement import IncomeStatement
from services.financials.balance_sheet import BalanceSheet
from services.financials.cash_flow import CashFlowStatement
from services.valuation.sotp.engine import SOTPEngine


def test_sotp_valuation_calculation() -> None:
    bs = BalanceSheet(
        total_assets=3_000_000.0,
        total_liabilities=1_200_000.0,
        total_equity=1_800_000.0,
        cash=300_000.0,
        short_term_debt=250_000.0,
        long_term_debt=300_000.0,
    )

    income = IncomeStatement(
        period="FY2025",
        revenue=1_000_000.0,
        ebitda=250_000.0,
        ebit=200_000.0,
        net_income=150_000.0,
        eps=45.0,
        shares_outstanding=1_000.0,
    )

    cashflow = CashFlowStatement(
        period="FY2025",
        operating_cash_flow=180_000.0,
        capital_expenditure=30_000.0,
        investing_cash_flow=0.0,
        financing_cash_flow=0.0,
    )

    fs = FinancialStatements(
        company_name="RELIANCE",
        ticker="RELIANCE.NS",
        currency="INR",
        fiscal_year="FY2025",
        income_statement=income,
        balance_sheet=bs,
        cash_flow_statement=cashflow,
    )

    engine = SOTPEngine()
    result = engine.calculate(
        fs,
        holding_discount=0.15,
    )

    assert result.symbol == "RELIANCE.NS"
    assert len(result.segments) == 4
    assert result.sum_of_segments_ev > 0.0
    assert result.conglomerate_equity_value > 0.0
    assert result.fair_value_per_share > 0.0
