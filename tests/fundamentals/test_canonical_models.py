from __future__ import annotations

import pytest
from services.fundamentals.canonical_models import CanonicalIncomeStatement, CanonicalBalanceSheet, CanonicalCashFlowStatement
from services.fundamentals.validator import CanonicalFinancialValidator

def test_canonical_models_and_validation() -> None:
    bs = CanonicalBalanceSheet(
        period="2025",
        cash=10000.0,
        total_current_assets=50000.0,
        property_plant_equipment=50000.0,
        total_assets=100000.0,
        total_current_liabilities=20000.0,
        long_term_debt=20000.0,
        total_liabilities=40000.0,
        shareholders_equity=60000.0
    )
    inc = CanonicalIncomeStatement(
        period="2025",
        revenue=150000.0,
        gross_profit=60000.0,
        operating_income=25000.0,
        net_income=18000.0,
        shares_outstanding=1000.0,
        eps=18.0
    )
    cf = CanonicalCashFlowStatement(
        period="2025",
        operating_cash_flow=30000.0,
        capital_expenditures=-10000.0,
        free_cash_flow=20000.0
    )

    bs_errors = CanonicalFinancialValidator.validate_balance_sheet(bs)
    inc_errors = CanonicalFinancialValidator.validate_income_statement(inc)
    analytics = CanonicalFinancialValidator.compute_analytics(bs, inc, cf)

    assert len(bs_errors) == 0
    assert len(inc_errors) == 0
    assert analytics["net_debt"] == 10000.0
    assert analytics["working_capital"] == 30000.0
    assert analytics["free_cash_flow"] == 20000.0
