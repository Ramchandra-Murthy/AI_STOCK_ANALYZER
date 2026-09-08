from __future__ import annotations

from services.financials.financial_statement import FinancialStatements
from services.financials.income_statement import IncomeStatement
from services.financials.balance_sheet import BalanceSheet
from services.financials.cash_flow import CashFlowStatement
from services.scoring.engine import AIScoringEngine


def test_ai_scoring_evaluation() -> None:
    fs = FinancialStatements(
        company_name="RELIANCE",
        ticker="RELIANCE.NS",
        currency="INR",
        fiscal_year="FY2025",
        income_statement=IncomeStatement(
            period="FY2025",
            revenue=1_000_000.0,
            ebitda=250_000.0,
            ebit=200_000.0,
            net_income=150_000.0,
            eps=45.0,
            shares_outstanding=1_000.0,
        ),
        balance_sheet=BalanceSheet(
            period="FY2025",
            total_assets=3_000_000.0,
            total_liabilities=1_200_000.0,
            total_equity=1_800_000.0,
            cash=300_000.0,
            short_term_debt=200_000.0,
            long_term_debt=300_000.0,
        ),
        cash_flow_statement=CashFlowStatement(
            period="FY2025",
            operating_cash_flow=180_000.0,
            capital_expenditure=30_000.0,
        ),
    )

    engine = AIScoringEngine()
    result = engine.evaluate(fs)

    assert result.symbol == "RELIANCE.NS"
    assert 0.0 <= result.composite_score <= 100.0
    assert result.growth_score > 0.0
    assert result.quality_score > 0.0
