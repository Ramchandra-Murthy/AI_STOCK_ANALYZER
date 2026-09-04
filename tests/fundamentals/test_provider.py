from __future__ import annotations

import pytest
from services.fundamentals.provider import YahooFinanceProvider, IFundamentalProvider


def test_yahoo_finance_provider() -> None:
    provider = YahooFinanceProvider()
    assert isinstance(provider, IFundamentalProvider)
    
    data = provider.download("RELIANCE.NS")
    assert data["symbol"] == "RELIANCE.NS"
    assert "income_statements" in data
    assert "balance_sheets" in data
    assert "cash_flows" in data

