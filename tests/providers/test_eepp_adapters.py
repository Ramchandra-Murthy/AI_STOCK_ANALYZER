from __future__ import annotations

from backend.providers.adapters.provider_adapters import AlphaVantageAdapter, YahooFinanceAdapter
from backend.providers.normalizer.event_normalizer import EventNormalizer


def test_event_normalization_engine() -> None:
    raw_payload = {"symbol": "tcs.ns", "price": "3450.75", "volume": "15000"}
    normalized = EventNormalizer.normalize_quote(raw_payload, "TestProvider")

    assert normalized["symbol"] == "TCS.NS"
    assert normalized["price"] == 3450.75
    assert normalized["volume"] == 15000
    assert normalized["provider"] == "TestProvider"
    assert normalized["normalized"] is True


def test_yahoo_finance_adapter_normalization() -> None:
    adapter = YahooFinanceAdapter()
    quote = adapter.fetch_latest_quote("RELIANCE.NS")

    assert quote["symbol"] == "RELIANCE.NS"
    assert quote["provider"] == "YahooFinance"
    assert quote["price"] == 3525.40


def test_alpha_vantage_adapter_normalization() -> None:
    adapter = AlphaVantageAdapter()
    quote = adapter.fetch_latest_quote("INFY.NS")

    assert quote["symbol"] == "INFY.NS"
    assert quote["provider"] == "AlphaVantage"
    assert quote["volume"] == 11500
