from __future__ import annotations

import pytest
from services.fundamentals.normalizer import FinancialNormalizer


def test_financial_normalizer() -> None:
    raw = {
        "symbol": "RELIANCE.NS",
        "provider": "YahooFinance",
        "income_statement": {"revenue": 5000.0, "operating_income": 1000.0, "ebit": 900.0, "net_income": 600.0, "eps": 10.0},
        "balance_sheet": {"total_assets": 10000.0, "total_liabilities": 4000.0, "shareholders_equity": 6000.0, "cash": 1000.0, "debt": 2000.0},
        "cash_flow": {"operating_cash_flow": 1200.0, "capex": 300.0, "free_cash_flow": 900.0, "investing_cash_flow": -300.0, "financing_cash_flow": -200.0},
    }

    normalizer = FinancialNormalizer()
    fs = normalizer.normalize(raw)

    assert fs.symbol == "RELIANCE.NS"
    assert fs.income_statements[0].revenue == 5000.0
    assert fs.balance_sheets[0].cash == 1000.0
    assert fs.cash_flows[0].free_cash_flow == 900.0
    assert fs.metadata["provider"] == "YahooFinance"
