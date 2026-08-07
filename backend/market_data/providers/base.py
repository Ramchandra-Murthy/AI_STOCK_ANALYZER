from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class MarketDataProvider(ABC):
    """Universal interface for all institutional market data providers."""

    @abstractmethod
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_ohlcv(self, symbol: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_news(self, symbol: str) -> List[Dict[str, Any]]:
        pass


class YahooMarketDataProvider(MarketDataProvider):
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        return {"symbol": symbol.upper(), "last": 3525.40, "volume": 12000, "provider": "yahoo"}

    def get_ohlcv(self, symbol: str) -> List[Dict[str, Any]]:
        return [{"symbol": symbol.upper(), "open": 3500.0, "high": 3530.0, "low": 3490.0, "close": 3525.40, "volume": 12000, "provider": "yahoo"}]

    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        return {"symbol": symbol.upper(), "name": "Sample Enterprise Corp", "sector": "Technology", "provider": "yahoo"}

    def get_news(self, symbol: str) -> List[Dict[str, Any]]:
        return [{"title": "Strong quarterly earnings reported", "provider": "yahoo"}]


class AlphaVantageMarketDataProvider(MarketDataProvider):
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        return {"ticker": symbol.upper(), "price": 3526.10, "volume": 11500, "provider": "alphavantage"}

    def get_ohlcv(self, symbol: str) -> List[Dict[str, Any]]:
        return [{"ticker": symbol.upper(), "open": 3501.0, "high": 3532.0, "low": 3492.0, "close": 3526.10, "volume": 11500, "provider": "alphavantage"}]

    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        return {"ticker": symbol.upper(), "company_name": "Sample Enterprise Corp", "industry": "Software", "provider": "alphavantage"}

    def get_news(self, symbol: str) -> List[Dict[str, Any]]:
        return [{"headline": "Expansion into new markets announced", "provider": "alphavantage"}]


class ProviderRegistry:
    """Centralized registry for dynamic provider dependency injection and failover."""
    _providers: Dict[str, MarketDataProvider] = {
        "yahoo": YahooMarketDataProvider(),
        "alphavantage": AlphaVantageMarketDataProvider()
    }

    @classmethod
    def register(cls, name: str, provider: MarketDataProvider) -> None:
        cls._providers[name.lower()] = provider

    @classmethod
    def get(cls, name: str) -> MarketDataProvider:
        provider = cls._providers.get(name.lower())
        if not provider:
            raise KeyError(f"Provider '{name}' is not registered in ProviderRegistry.")
        return provider