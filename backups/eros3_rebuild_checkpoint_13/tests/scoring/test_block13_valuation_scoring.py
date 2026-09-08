from services.financials.financial_statement import (
    FinancialStatements,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
)
from services.scoring.engine import AIScoringEngine


def test_block13_valuation_scoring_integration() -> None:
    income = IncomeStatement(
        revenue=120000.0,
        cost_of_goods_sold=70000.0,
        ebitda=30000.0,
        ebit=24000.0,
        net_income=18000.0,
        eps=18.0,
        shares_outstanding=1000.0,
    )

    balance = BalanceSheet(
        cash=25000.0,
        cash_equivalents=5000.0,
        accounts_receivable=15000.0,
        inventory=10000.0,
        total_assets=220000.0,
        total_liabilities=70000.0,
        total_equity=150000.0,
        short_term_debt=5000.0,
        long_term_debt=15000.0,
    )

    cashflow = CashFlowStatement(
        operating_cash_flow=22000.0,
        capital_expenditure=6000.0,
        beginning_cash=20000.0,
        net_change_in_cash=5000.0,
        ending_cash=25000.0,
    )

    statements = FinancialStatements(
        company_name="Larsen & Toubro",
        ticker="LT.NS",
        currency="INR",
        fiscal_year="FY2025",
        income_statement=income,
        balance_sheet=balance,
        cash_flow_statement=cashflow,
        periods=[],
    )

    engine = AIScoringEngine()
    result = engine.evaluate(statements)

    # --------------------------------------------------------
    # RESULT IDENTITY
    # --------------------------------------------------------

    assert result.symbol == "LT.NS"

    # --------------------------------------------------------
    # SCORE CONTRACT
    # --------------------------------------------------------

    assert 0.0 <= result.composite_score <= 100.0
    assert 0.0 <= result.valuation_score <= 100.0

    # --------------------------------------------------------
    # SCORING ENGINE CONTRACT
    # --------------------------------------------------------

    assert result.breakdown_details["engine_version"] == \
        "EROS-3.0-BLOCK-15"

    assert "valuation_engine" in result.breakdown_details

    valuation = result.breakdown_details["valuation_engine"]

    # --------------------------------------------------------
    # CANONICAL VALUATION CONTRACT
    # --------------------------------------------------------

    assert valuation["method"] == "DCF"
    assert valuation["status"] == "SUCCESS"

    assert "enterprise_value" in valuation
    assert "equity_value" in valuation
    assert "implied_share_price" in valuation
    assert "details" in valuation
    assert "valuation_score" in valuation

    assert float(valuation["enterprise_value"]) >= 0.0
    assert float(valuation["equity_value"]) >= 0.0
    assert float(valuation["implied_share_price"]) > 0.0

    assert 0.0 <= float(valuation["valuation_score"]) <= 100.0
