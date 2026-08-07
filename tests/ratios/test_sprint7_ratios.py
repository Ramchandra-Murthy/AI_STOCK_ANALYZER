from __future__ import annotations

import pytest
from services.fundamentals.canonical_models import CanonicalIncomeStatement, CanonicalBalanceSheet
from services.ratios.liquidity import LiquidityRatioEngine
from services.ratios.leverage import LeverageRatioEngine
from services.ratios.efficiency import EfficiencyRatioEngine

def test_sprint7_ratio_sub_engines() -> None:
    inc = CanonicalIncomeStatement(
        period="2025",
        revenue=120000.0,
        cost_of_revenue=70000.0,
        operating_income=25000.0,
        ebit=25000.0,
        ebitda=30000.0,
        interest_expense=2500.0,
        net_income=18000.0
    )
    bs = CanonicalBalanceSheet(
        period="2025",
        cash=15000.0,
        accounts_receivable=20000.0,
        inventory=15000.0,
        total_current_assets=55000.0,
        total_assets=150000.0,
        accounts_payable=12000.0,
        total_current_liabilities=25000.0,
        long_term_debt=30000.0,
        total_liabilities=55000.0,
        shareholders_equity=95000.0
    )

    liq = LiquidityRatioEngine.compute(inc, bs, symbol="TEST.NS")
    lev = LeverageRatioEngine.compute(inc, bs, symbol="TEST.NS")
    eff = EfficiencyRatioEngine.compute(inc, bs, symbol="TEST.NS")

    assert liq.metrics["current_ratio"] > 1.0
    assert lev.metrics["interest_coverage"] == 10.0
    assert eff.metrics["cash_conversion_cycle"] >= 0.0
