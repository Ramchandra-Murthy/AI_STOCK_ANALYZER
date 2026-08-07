from __future__ import annotations

import pytest
from services.valuation.blended_engine import BlendedValuationEngine
from services.fundamentals.models import FinancialStatements, IncomeStatement, BalanceSheet, CashFlowStatement

def test_blended_valuation_engine() -> None:
    engine = BlendedValuationEngine()
    
    fin = FinancialStatements(
        symbol="RELIANCE.NS",
        income_statements=[IncomeStatement(period="2025", revenue=100000.0, operating_income=15000.0, ebit=15000.0, net_income=10000.0, eps=10.0)],
        balance_sheets=[BalanceSheet(total_assets=200000.0, total_liabilities=100000.0, total_equity=100000.0, cash_and_equivalents=10000.0, total_debt=60000.0)],
        cash_flow_statements=[CashFlowStatement(operating_cash_flow=18000.0, capital_expenditure=5000.0, free_cash_flow=13000.0)]
    )

    projections = [13000.0, 14500.0, 16000.0, 18000.0, 20000.0]
    result = engine.evaluate(
        symbol="RELIANCE.NS",
        fcff_projections=projections,
        wacc=0.10,
        terminal_growth_rate=0.04,
        net_debt=50000.0,
        shares_outstanding=1000.0,
        current_price=1400.0,
        financials=fin
    )

    assert result.symbol == "RELIANCE.NS"
    assert result.blended_fair_value > 0
    assert "DCF" in result.model_weights
