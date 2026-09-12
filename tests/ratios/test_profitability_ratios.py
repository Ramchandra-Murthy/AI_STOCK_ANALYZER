from __future__ import annotations

from services.fundamentals.canonical_models import CanonicalBalanceSheet, CanonicalIncomeStatement
from services.ratios.profitability import ProfitabilityRatioEngine


def test_profitability_ratio_engine() -> None:
    inc = CanonicalIncomeStatement(
        period="2025",
        revenue=100000.0,
        cost_of_revenue=40000.0,
        gross_profit=60000.0,
        operating_income=25000.0,
        ebit=25000.0,
        ebitda=30000.0,
        net_income=18000.0,
    )
    bs = CanonicalBalanceSheet(
        period="2025",
        total_assets=120000.0,
        total_current_liabilities=20000.0,
        shareholders_equity=75000.0,
    )

    result = ProfitabilityRatioEngine.compute(inc, bs, symbol="TEST.NS")

    assert result.symbol == "TEST.NS"
    assert result.category_name == "Profitability"
    assert result.metrics["gross_margin"] == 60.0
    assert result.metrics["net_margin"] == 18.0
    assert result.metrics["roe"] > 0.0
    assert result.metrics["roic"] > 0.0
