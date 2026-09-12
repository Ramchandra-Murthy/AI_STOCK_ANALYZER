from __future__ import annotations

import pytest

from backend.events.normalizer import CanonicalEventNormalizer
from backend.market_data.providers.base import (
    AlphaVantageMarketDataProvider,
    ProviderRegistry,
    YahooMarketDataProvider,
)


def test_provider_registry_and_yahoo() -> None:
    provider = ProviderRegistry.get("yahoo")
    assert isinstance(provider, YahooMarketDataProvider)
    quote = provider.get_quote("tcs.ns")
    assert quote["symbol"] == "TCS.NS"
    assert quote["provider"] == "yahoo"

    normalized = CanonicalEventNormalizer.normalize_quote(quote)
    assert normalized["symbol"] == "TCS.NS"
    assert normalized["price"] == 3525.40
    assert normalized["normalized"] is True


def test_provider_registry_and_alphavantage() -> None:
    provider = ProviderRegistry.get("alphavantage")
    assert isinstance(provider, AlphaVantageMarketDataProvider)
    quote = provider.get_quote("infy.ns")
    assert quote["ticker"] == "INFY.NS"
    assert quote["provider"] == "alphavantage"

    # Map ticker to symbol for normalization testing
    quote["symbol"] = quote.pop("ticker")
    quote["price"] = quote.pop("price")
    normalized = CanonicalEventNormalizer.normalize_quote(quote)
    assert normalized["symbol"] == "INFY.NS"
    assert normalized["price"] == 3526.10
    assert normalized["provider"] == "alphavantage"


def test_registry_missing_provider_raises_error() -> None:
    with pytest.raises(KeyError):
        ProviderRegistry.get("nonexistent_broker")
