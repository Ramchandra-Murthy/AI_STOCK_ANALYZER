from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from backend.market_data.providers.base import (
    AlphaVantageMarketDataProvider,
    ProviderRegistry,
    YahooMarketDataProvider,
)
from backend.events.normalizer import CanonicalEventNormalizer


class FakeTicker:
    @property
    def fast_info(self):
        return {
            "last_price": 3525.40,
            "previous_close": 3500.0,
            "last_volume": 12000,
        }

    def history(self, **kwargs):
        now = datetime.now(timezone.utc)
        return pd.DataFrame(
            {
                "Open": [3500.0],
                "High": [3530.0],
                "Low": [3490.0],
                "Close": [3525.40],
                "Volume": [12000],
            },
            index=pd.DatetimeIndex([now]),
        )

    def get_info(self):
        return {
            "longName": "Test Company",
            "sector": "Technology",
            "industry": "Software",
        }

    def get_news(self, count=10):
        return [{"title": "Test headline"}]


def test_provider_registry_and_yahoo(monkeypatch):
    provider = ProviderRegistry.get("yahoo")
    assert isinstance(provider, YahooMarketDataProvider)
    monkeypatch.setattr(provider, "_ticker", lambda symbol: FakeTicker())

    quote = provider.get_quote("tcs.ns")
    assert quote["symbol"] == "TCS.NS"
    assert quote["provider"] == "yahoo"
    assert quote["source"] == "yfinance-live-api"
    assert quote["last"] == 3525.40

    normalized = CanonicalEventNormalizer.normalize_quote(
        {
            "symbol": quote["symbol"],
            "price": quote["last"],
            "provider": quote["provider"],
        }
    )
    assert normalized["symbol"] == "TCS.NS"
    assert normalized["price"] == 3525.40
    assert normalized["normalized"] is True


def test_provider_registry_and_alphavantage_requires_real_configuration(monkeypatch):
    provider = ProviderRegistry.get("alphavantage")
    assert isinstance(provider, AlphaVantageMarketDataProvider)
    monkeypatch.delenv("ALPHAVANTAGE_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="ALPHAVANTAGE_API_KEY"):
        provider.get_quote("INFY.NS")


def test_registry_missing_provider_raises_error():
    with pytest.raises(KeyError):
        ProviderRegistry.get("nonexistent_broker")
