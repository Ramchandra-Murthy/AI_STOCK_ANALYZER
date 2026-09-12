from __future__ import annotations

import logging
from typing import Any

from backend.providers.normalizer.event_normalizer import EventNormalizer

logger = logging.getLogger(__name__)


class BaseProviderAdapter:
    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name

    def fetch_latest_quote(self, symbol: str) -> dict[str, Any]:
        raise NotImplementedError


class YahooFinanceAdapter(BaseProviderAdapter):
    def __init__(self) -> None:
        super().__init__("YahooFinance")

    def fetch_latest_quote(self, symbol: str) -> dict[str, Any]:
        # Simulated raw response from Yahoo Finance API schema
        raw_data = {
            "symbol": symbol,
            "last": 3525.40,
            "qty": 12000,
            "timestamp": "2026-04-07T10:00:00Z",
        }
        return EventNormalizer.normalize_quote(raw_data, self.provider_name)


class AlphaVantageAdapter(BaseProviderAdapter):
    def __init__(self) -> None:
        super().__init__("AlphaVantage")

    def fetch_latest_quote(self, symbol: str) -> dict[str, Any]:
        # Simulated raw response from Alpha Vantage API schema
        raw_data = {
            "ticker": symbol,
            "price": 3526.10,
            "volume": 11500,
            "timestamp": "2026-04-07T10:00:01Z",
        }
        return EventNormalizer.normalize_quote(raw_data, self.provider_name)
