from __future__ import annotations

from services.financials.income_statement import IncomeStatement
from services.financials.balance_sheet import BalanceSheet
from services.financials.cash_flow import CashFlowStatement
from services.financials.financial_statement import FinancialStatements
from services.valuation.relative.engine import RelativeValuationEngine


def test_relative_valuation_calculation() -> None:
    inc = IncomeStatement(
        revenue=1000000.0,
        ebitda=250000.0,
        ebit=200000.0,
        net_income=150000.0,
        eps=45.0,
        shares_outstanding=1000.0,
    )

    bs = BalanceSheet(
        total_assets=3000000.0,
        total_liabilities=1200000.0,
        total_equity=1800000.0,
        cash=300000.0,
        short_term_debt=200000.0,
        long_term_debt=300000.0,
    )

    cf = CashFlowStatement(
        operating_cash_flow=180000.0,
        capital_expenditure=30000.0,
        investing_cash_flow=-30000.0,
        financing_cash_flow=0.0,
        dividends_paid=0.0,
        net_change_in_cash=150000.0,
        beginning_cash=150000.0,
        ending_cash=300000.0,
    )

    fs = FinancialStatements(
        company_name="Reliance Industries",
        ticker="RELIANCE.NS",
        currency="INR",
        fiscal_year="FY2025",
        income_statement=inc,
        balance_sheet=bs,
        cash_flow_statement=cf,
    )

    engine = RelativeValuationEngine()
    result = engine.evaluate(fs, current_price=1400.0)

    assert result.symbol == "RELIANCE.NS"
    assert result.pe_ratio > 0.0
    assert result.ev_ebitda > 0.0
    assert result.blend_relative_value > 0.0
    assert "sector_pe" in result.comparison_benchmarks
