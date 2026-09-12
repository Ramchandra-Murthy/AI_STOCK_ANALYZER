from __future__ import annotations

from datetime import datetime

import pytest

from backend.providers.base_provider import ProviderError
from backend.providers.implementations import (
    AlphaVantageProvider,
    YahooFinanceProvider,
)
from backend.providers.selector import ProviderSelectionEngine


def test_yahoo_provider_operations() -> None:
    provider = YahooFinanceProvider()
    assert provider.check_health() is True

    statements = provider.fetch_financial_statements("TCS.NS")
    assert statements["symbol"] == "TCS.NS"
    assert statements["eps"] > 0

    prices = provider.fetch_historical_prices("TCS.NS", datetime(2026, 1, 1), datetime(2026, 7, 1))
    assert len(prices["prices"]) > 0


def test_provider_failover_routing() -> None:
    # First provider is intentionally misconfigured or will fail, second succeeds
    yahoo = YahooFinanceProvider()
    alpha = AlphaVantageProvider()

    # Mock yahoo to fail
    def failing_fetch(symbol: str) -> Dict[str, Any]:
        raise RuntimeError("Yahoo API Down")

    yahoo.fetch_financial_statements = failing_fetch

    selector = ProviderSelectionEngine(providers=[yahoo, alpha])
    result = selector.execute_with_failover("fetch_financial_statements", "INFY.NS")

    assert result["symbol"] == "INFY.NS"
    assert result["eps"] == 116.0


def test_all_providers_fail_raises_error() -> None:
    yahoo = YahooFinanceProvider()

    def failing_fetch(symbol: str) -> Dict[str, Any]:
        raise RuntimeError("Service Unavailable")

    yahoo.fetch_financial_statements = failing_fetch
    selector = ProviderSelectionEngine(providers=[yahoo])

    with pytest.raises(ProviderError):
        selector.execute_with_failover("fetch_financial_statements", "RELIANCE.NS")
