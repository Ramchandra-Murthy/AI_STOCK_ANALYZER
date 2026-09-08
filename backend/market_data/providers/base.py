from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List


class MarketDataProvider(ABC):
    """Universal interface for institutional market-data providers."""

    @abstractmethod
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_ohlcv(self, symbol: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_news(self, symbol: str) -> List[Dict[str, Any]]:
        raise NotImplementedError


class YahooMarketDataProvider(MarketDataProvider):
    """Real Yahoo Finance provider; never returns fabricated market values."""

    def _ticker(self, symbol: str):
        import yfinance as yf

        return yf.Ticker(str(symbol).strip().upper())

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        normalized = str(symbol).strip().upper()
        ticker = self._ticker(normalized)
        fast = ticker.fast_info
        price = fast.get("last_price")
        previous = fast.get("previous_close")

        if price is None or float(price) <= 0:
            raise RuntimeError(f"No valid live price returned for {normalized}")

        return {
            "symbol": normalized,
            "last": float(price),
            "previous_close": (
                float(previous) if previous is not None and float(previous) > 0 else None
            ),
            "volume": int(fast.get("last_volume") or 0),
            "provider": "yahoo",
            "source": "yfinance-live-api",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_ohlcv(self, symbol: str) -> List[Dict[str, Any]]:
        normalized = str(symbol).strip().upper()
        history = self._ticker(normalized).history(
            period="5d",
            interval="1d",
            auto_adjust=False,
            repair=True,
            timeout=10,
        )
        if history is None or history.empty:
            raise RuntimeError(f"No OHLCV returned for {normalized}")

        rows: List[Dict[str, Any]] = []
        for idx, row in history.iterrows():
            rows.append(
                {
                    "symbol": normalized,
                    "date": idx.isoformat(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"] or 0),
                    "provider": "yahoo",
                }
            )
        return rows

    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        normalized = str(symbol).strip().upper()
        info = self._ticker(normalized).get_info()
        if not info:
            raise RuntimeError(f"No company profile returned for {normalized}")
        return {
            "symbol": normalized,
            "name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "provider": "yahoo",
        }

    def get_news(self, symbol: str) -> List[Dict[str, Any]]:
        normalized = str(symbol).strip().upper()
        return [
            {
                "title": item.get("title") or item.get("content", {}).get("title"),
                "provider": "yahoo",
                "raw": item,
            }
            for item in (self._ticker(normalized).get_news(count=10) or [])
        ]


class AlphaVantageMarketDataProvider(MarketDataProvider):
    """
    Real Alpha Vantage provider boundary.

    No API key means the provider fails explicitly; it never substitutes sample
    prices. Configure ALPHAVANTAGE_API_KEY before putting this provider in a
    failover chain.
    """

    def _key(self) -> str:
        key = os.getenv("ALPHAVANTAGE_API_KEY", "").strip()
        if not key:
            raise RuntimeError("ALPHAVANTAGE_API_KEY is not configured")
        return key

    def _request(self, symbol: str, function: str) -> Dict[str, Any]:
        import json
        from urllib.parse import urlencode
        from urllib.request import urlopen

        params = urlencode(
            {
                "function": function,
                "symbol": symbol,
                "apikey": self._key(),
            }
        )
        with urlopen(
            f"https://www.alphavantage.co/query?{params}",
            timeout=10,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if "Error Message" in payload or "Note" in payload:
            raise RuntimeError(str(payload.get("Error Message") or payload.get("Note")))
        return payload

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        normalized = str(symbol).strip().upper()
        payload = self._request(normalized, "GLOBAL_QUOTE")
        quote = payload.get("Global Quote") or {}
        price = float(quote.get("05. price") or 0)
        if price <= 0:
            raise RuntimeError(f"No valid Alpha Vantage price returned for {normalized}")
        return {
            "symbol": normalized,
            "last": price,
            "previous_close": None,
            "volume": int(float(quote.get("06. volume") or 0)),
            "provider": "alphavantage",
            "source": "alphavantage-api",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_ohlcv(self, symbol: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("Alpha Vantage OHLCV adapter is not implemented")

    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError("Alpha Vantage company profile adapter is not implemented")

    def get_news(self, symbol: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("Alpha Vantage news adapter is not implemented")


class ProviderRegistry:
    """Centralized registry for dynamic provider dependency injection and failover."""

    _providers: Dict[str, MarketDataProvider] = {
        "yahoo": YahooMarketDataProvider(),
        "alphavantage": AlphaVantageMarketDataProvider(),
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
