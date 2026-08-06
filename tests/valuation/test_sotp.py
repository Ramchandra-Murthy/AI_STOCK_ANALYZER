from __future__ import annotations

import pytest
from services.fundamentals.models import FinancialStatements, BalanceSheet
from services.valuation.sotp.engine import SOTPEngine


def test_sotp_valuation_calculation() -> None:
    bs = BalanceSheet(period="FY2025", total_assets=3000000.0, total_liabilities=1200000.0, shareholders_equity=1800000.0, cash=300000.0, debt=550000.0)
    fs = FinancialStatements(symbol="RELIANCE.NS", balance_sheets=[bs])

    engine = SOTPEngine()
    result = engine.calculate(fs, holding_discount=0.15)

    assert result.symbol == "RELIANCE.NS"
    assert len(result.segments) == 4
    assert result.sum_of_segments_ev > 0.0
    assert result.conglomerate_equity_value > 0.0
    assert result.fair_value_per_share > 0.0
