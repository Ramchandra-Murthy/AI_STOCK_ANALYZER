from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from backend.providers.base_provider import BaseDataProvider

logger = logging.getLogger(__name__)


class YahooFinanceProvider(BaseDataProvider):
    def __init__(self) -> None:
        super().__init__(provider_name="YahooFinance")

    def fetch_historical_prices(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        self.logger.info("Fetching historical prices for %s from Yahoo Finance", symbol)
        return {
            "symbol": symbol,
            "provider": self.provider_name,
            "prices": [
                {"date": "2026-06-01", "close": 2450.0},
                {"date": "2026-07-01", "close": 2500.0},
            ],
        }

    def fetch_financial_statements(self, symbol: str) -> dict[str, Any]:
        self.logger.info("Fetching financial statements for %s from Yahoo Finance", symbol)
        return {
            "symbol": symbol,
            "eps": 115.50,
            "revenue": 15000000000.0,
            "net_income": 2500000000.0,
        }

    def check_health(self) -> bool:
        return True


class AlphaVantageProvider(BaseDataProvider):
    def __init__(self, api_key: str = "demo_key") -> None:
        super().__init__(provider_name="AlphaVantage", api_key=api_key)

    def fetch_historical_prices(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        self.logger.info("Fetching historical prices for %s from Alpha Vantage", symbol)
        return {
            "symbol": symbol,
            "provider": self.provider_name,
            "prices": [{"date": "2026-07-01", "close": 2510.0}],
        }

    def fetch_financial_statements(self, symbol: str) -> dict[str, Any]:
        return {"symbol": symbol, "eps": 116.0, "revenue": 15100000000.0}

    def check_health(self) -> bool:
        return bool(self.api_key)


class NSEIndiaProvider(BaseDataProvider):
    def __init__(self) -> None:
        super().__init__(provider_name="NSEIndia")

    def fetch_historical_prices(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        return {
            "symbol": symbol,
            "provider": self.provider_name,
            "prices": [{"date": "2026-07-01", "close": 2495.0}],
        }

    def fetch_financial_statements(self, symbol: str) -> dict[str, Any]:
        return {"symbol": symbol, "eps": 115.0}

    def check_health(self) -> bool:
        return True
