from __future__ import annotations

from services.fundamentals.models import FinancialStatements
from services.financials.balance_sheet import BalanceSheet
from services.valuation.sotp.engine import SOTPEngine


def test_sotp_valuation_calculation() -> None:
    bs = BalanceSheet(
        total_assets=3_000_000.0,
        total_liabilities=1_200_000.0,
        total_equity=1_800_000.0,
        cash=300_000.0,
        short_term_debt=250_000.0,
        long_term_debt=300_000.0,
    )

    fs = FinancialStatements(
        symbol="RELIANCE.NS",
        balance_sheets=[bs],
    )

    engine = SOTPEngine()
    result = engine.calculate(
        fs,
        holding_discount=0.15,
    )

    assert result.symbol == "RELIANCE.NS"
    assert len(result.segments) == 4
    assert result.sum_of_segments_ev > 0.0
    assert result.conglomerate_equity_value > 0.0
    assert result.fair_value_per_share > 0.0
