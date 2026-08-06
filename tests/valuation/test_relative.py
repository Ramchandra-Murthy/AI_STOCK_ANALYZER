from __future__ import annotations

import pytest
from services.fundamentals.models import FinancialStatements, IncomeStatement, BalanceSheet
from services.valuation.relative.engine import RelativeValuationEngine


def test_relative_valuation_calculation() -> None:
    inc = IncomeStatement(period="FY2025", revenue=1000000.0, operating_income=220000.0, ebit=200000.0, net_income=150000.0, eps=45.0)
    bs = BalanceSheet(period="FY2025", total_assets=3000000.0, total_liabilities=1200000.0, shareholders_equity=1800000.0, cash=300000.0, debt=500000.0)
    fs = FinancialStatements(symbol="RELIANCE.NS", income_statements=[inc], balance_sheets=[bs])

    engine = RelativeValuationEngine()
    result = engine.evaluate(fs, current_price=1400.0)

    assert result.symbol == "RELIANCE.NS"
    assert result.pe_ratio > 0.0
    assert result.ev_ebitda > 0.0
    assert result.blend_relative_value > 0.0
    assert "sector_pe" in result.comparison_benchmarks
