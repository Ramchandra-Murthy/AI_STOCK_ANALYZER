from services.financials.parser import repository
from services.financials.financial_statement import (
    FinancialStatements,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    PeriodFinancials,
)
from services.scoring.engine import AIScoringEngine

def test_block11_historical_growth_scoring() -> None:
    bal = BalanceSheet(cash=10000.0, cash_equivalents=2000.0, accounts_receivable=15000.0, inventory=10000.0, total_assets=200000.0, total_liabilities=100000.0, total_equity=100000.0, short_term_debt=20000.0, long_term_debt=40000.0)

    inc1 = IncomeStatement(revenue=80000.0, cost_of_goods_sold=48000.0, ebitda=15000.0, ebit=12000.0, net_income=8000.0, eps=8.0, shares_outstanding=1000.0)
    cf1 = CashFlowStatement(operating_cash_flow=14000.0, capital_expenditure=4000.0, beginning_cash=8000.0, net_change_in_cash=1000.0, ending_cash=9000.0)
    p1 = PeriodFinancials(period="FY2023", income_statement=inc1, balance_sheet=bal, cash_flow_statement=cf1)

    inc2 = IncomeStatement(revenue=90000.0, cost_of_goods_sold=54000.0, ebitda=18000.0, ebit=14000.0, net_income=9000.0, eps=9.0, shares_outstanding=1000.0)
    cf2 = CashFlowStatement(operating_cash_flow=16000.0, capital_expenditure=4500.0, beginning_cash=9000.0, net_change_in_cash=1000.0, ending_cash=10000.0)
    p2 = PeriodFinancials(period="FY2024", income_statement=inc2, balance_sheet=bal, cash_flow_statement=cf2)

    inc3 = IncomeStatement(revenue=100000.0, cost_of_goods_sold=60000.0, ebitda=20000.0, ebit=15000.0, net_income=10000.0, eps=10.0, shares_outstanding=1000.0)
    cf3 = CashFlowStatement(operating_cash_flow=18000.0, capital_expenditure=5000.0, beginning_cash=10000.0, net_change_in_cash=1000.0, ending_cash=11000.0)
    p3 = PeriodFinancials(period="FY2025", income_statement=inc3, balance_sheet=bal, cash_flow_statement=cf3)

    income = IncomeStatement(revenue=100000.0, cost_of_goods_sold=60000.0, ebitda=20000.0, ebit=15000.0, net_income=10000.0, eps=10.0, shares_outstanding=1000.0)
    balance = BalanceSheet(cash=10000.0, cash_equivalents=2000.0, accounts_receivable=15000.0, inventory=10000.0, total_assets=200000.0, total_liabilities=100000.0, total_equity=100000.0, short_term_debt=20000.0, long_term_debt=40000.0)
    cashflow = CashFlowStatement(operating_cash_flow=18000.0, capital_expenditure=5000.0, beginning_cash=9000.0, net_change_in_cash=1000.0, ending_cash=10000.0)

    statements = FinancialStatements(
        company_name="Reliance Industries",
        ticker="RELIANCE.NS",
        currency="INR",
        fiscal_year="FY2025",
        income_statement=income,
        balance_sheet=balance,
        cash_flow_statement=cashflow,
        periods=[p1, p2, p3],
    )

    engine = AIScoringEngine()
    result = engine.evaluate(statements)

    assert result.symbol == "RELIANCE.NS"
    assert 0.0 <= result.growth_score <= 100.0
    assert result.growth_score != 60.0
    assert "growth_engine" in result.breakdown_details
    assert "EROS-3.0" in result.breakdown_details["engine_version"]

    repository().clear()
