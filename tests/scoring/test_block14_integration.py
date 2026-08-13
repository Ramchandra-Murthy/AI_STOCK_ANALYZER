from services.financials.parser import repository
from services.financials.financial_statement import (
    FinancialStatements,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
)
from services.market_data.models import PriceRecord
from services.scoring.engine import AIScoringEngine

def test_block14_ai_scoring_integration() -> None:
    income = IncomeStatement(
        revenue=150000.0,
        cost_of_goods_sold=85000.0,
        ebitda=40000.0,
        ebit=32000.0,
        net_income=24000.0,
        eps=24.0,
        shares_outstanding=1000.0,
    )
    balance = BalanceSheet(
        cash=30000.0,
        cash_equivalents=10000.0,
        accounts_receivable=20000.0,
        inventory=12000.0,
        total_assets=250000.0,
        total_liabilities=90000.0,
        total_equity=160000.0,
        short_term_debt=10000.0,
        long_term_debt=20000.0,
    )
    cashflow = CashFlowStatement(
        operating_cash_flow=28000.0,
        capital_expenditure=7000.0,
        beginning_cash=25000.0,
        net_change_in_cash=5000.0,
        ending_cash=30000.0,
    )

    statements = FinancialStatements(
        company_name="Tata Consultancy Services",
        ticker="TCS.NS",
        currency="INR",
        fiscal_year="FY2025",
        income_statement=income,
        balance_sheet=balance,
        cash_flow_statement=cashflow,
        periods=[],
    )

    records = [
        PriceRecord(
            date=f"2026-06-{i+1:02d}",
            open=3000.0 + i * 10,
            high=3020.0 + i * 10,
            low=2990.0 + i * 10,
            close=3010.0 + i * 10,
            volume=1500000,
        )
        for i in range(40)
    ]

    engine = AIScoringEngine()
    result = engine.evaluate(statements, market_records=records)

    assert result.symbol == "TCS.NS"
    assert 0.0 <= result.composite_score <= 100.0
    assert 0.0 <= result.momentum_score <= 100.0
    assert result.breakdown_details["engine_version"] == "EROS-3.0-BLOCK-15"
    assert "momentum_engine" in result.breakdown_details
    assert result.breakdown_details["momentum_engine"]["engine_version"] == "EROS-3.0-BLOCK-14"

    repository().clear()

