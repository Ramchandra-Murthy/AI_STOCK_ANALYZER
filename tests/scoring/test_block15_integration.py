from services.financials.financial_statement import (
    BalanceSheet,
    CashFlowStatement,
    FinancialStatements,
    IncomeStatement,
)
from services.financials.parser import repository
from services.risk_management.models import PortfolioRiskProfile
from services.scoring.engine import AIScoringEngine


def test_block15_ai_scoring_integration() -> None:
    income = IncomeStatement(
        revenue=180000.0,
        cost_of_goods_sold=95000.0,
        ebitda=45000.0,
        ebit=36000.0,
        net_income=28000.0,
        eps=28.0,
        shares_outstanding=1000.0,
    )
    balance = BalanceSheet(
        cash=35000.0,
        cash_equivalents=15000.0,
        accounts_receivable=22000.0,
        inventory=14000.0,
        total_assets=280000.0,
        total_liabilities=95000.0,
        total_equity=185000.0,
        short_term_debt=8000.0,
        long_term_debt=18000.0,
    )
    cashflow = CashFlowStatement(
        operating_cash_flow=32000.0,
        capital_expenditure=8000.0,
        beginning_cash=30000.0,
        net_change_in_cash=5000.0,
        ending_cash=35000.0,
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

    profile = PortfolioRiskProfile(
        portfolio_id="INFY-RISK-01",
        expected_volatility=0.16,
        value_at_risk=0.04,
        expected_shortfall=0.07,
        concentration_score=80.0,
        liquidity_score=90.0,
        diversification_score=85.0,
        resilience_score=92.0,
    )

    engine = AIScoringEngine()
    result = engine.evaluate(statements, risk_profile=profile)

    assert result.symbol == "INFY.NS"
    assert 0.0 <= result.composite_score <= 100.0
    assert 0.0 <= result.risk_score <= 100.0
    assert result.breakdown_details["engine_version"] == "EROS-3.0-BLOCK-15"
    assert "risk_engine" in result.breakdown_details
    assert result.breakdown_details["risk_engine"]["engine_version"] == "EROS-3.0-BLOCK-15"

    repository().clear()
