from __future__ import annotations

from services.ratios.quality_engine import AdvancedQualityEngine
from services.financials.income_statement import IncomeStatement
from services.financials.balance_sheet import BalanceSheet


def test_advanced_quality_engine() -> None:
    bs = BalanceSheet(
        period="2025",
        total_assets=100000.0,
        total_liabilities=40000.0,
        total_equity=60000.0,
        cash=15000.0,
        long_term_debt=20000.0,
    )

    inc = IncomeStatement(
        period="2025",
        revenue=120000.0,
        total_operating_income=18000.0,
        ebit=18000.0,
        net_income=12000.0,
        eps=12.0,
    )

    z_score = AdvancedQualityEngine.compute_altman_z(bs, inc)
    ccc_metrics = AdvancedQualityEngine.compute_cash_conversion_cycle(bs, inc)

    assert z_score > 0.0
    assert "cash_conversion_cycle" in ccc_metrics
    assert ccc_metrics["cash_conversion_cycle"] >= 0.0
