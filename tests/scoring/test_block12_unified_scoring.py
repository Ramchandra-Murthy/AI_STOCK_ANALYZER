from services.financials.parser import repository
from services.financials.financial_statement import (
    FinancialStatements,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
)
from services.scoring.engine import AIScoringEngine

def test_block12_unified_scoring_engine() -> None:
    income = IncomeStatement(
        revenue=100000.0,
        cost_of_goods_sold=60000.0,
        ebitda=25000.0,
        ebit=20000.0,
        net_income=15000.0,
        eps=15.0,
        shares_outstanding=1000.0,
    )
    balance = BalanceSheet(
        cash=20000.0,
        cash_equivalents=5000.0,
        accounts_receivable=15000.0,
        inventory=10000.0,
        total_assets=200000.0,
        total_liabilities=80000.0,
        total_equity=120000.0,
        short_term_debt=10000.0,
        long_term_debt=20000.0,
    )
    cashflow = CashFlowStatement(
        operating_cash_flow=18000.0,
        capital_expenditure=5000.0,
        beginning_cash=15000.0,
        net_change_in_cash=5000.0,
        ending_cash=20000.0,
    )

    statements = FinancialStatements(
        company_name="Infosys Limited",
        ticker="INFY.NS",
        currency="INR",
        fiscal_year="FY2025",
        income_statement=income,
        balance_sheet=balance,
        cash_flow_statement=cashflow,
        periods=[],
    )

    engine = AIScoringEngine()
    result = engine.evaluate(statements)

    assert result.symbol == "INFY.NS"
    assert 0.0 <= result.composite_score <= 100.0
    assert "EROS-3.0" in result.breakdown_details["engine_version"]
    assert "fundamental_engine" in result.breakdown_details
    assert "growth_engine" in result.breakdown_details

    repository().clear()

