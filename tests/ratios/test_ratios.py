from __future__ import annotations

import pytest
from services.ratios.engine import FinancialRatioEngine
from services.fundamentals.models import FinancialStatements, IncomeStatement, BalanceSheet, CashFlowStatement

def test_financial_ratio_engine() -> None:
    engine = FinancialRatioEngine()
    
    fin = FinancialStatements(
        symbol="RELIANCE.NS",
        income_statements=[
            IncomeStatement(period="2025", revenue=100000.0, operating_income=20000.0, ebit=18000.0, net_income=12000.0, eps=12.0)
        ],
        balance_sheets=[
            BalanceSheet(period="2025", total_assets=250000.0, total_liabilities=100000.0, shareholders_equity=150000.0, cash=20000.0, debt=50000.0)
        ],
        cash_flows=[
            CashFlowStatement(period="2025", operating_cash_flow=22000.0, capex=5000.0, free_cash_flow=17000.0, investing_cash_flow=-6000.0, financing_cash_flow=-8000.0)
        ]
    )

    ratios = engine.compute_ratios(fin)

    assert ratios.symbol == "RELIANCE.NS"
    assert ratios.profitability["net_margin"] > 0
    assert ratios.solvency["debt_to_equity"] > 0
    assert ratios.quality_scores["piotroski_f_score"] == 7.0
