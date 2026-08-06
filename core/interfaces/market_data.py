from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, runtime_checkable
import pandas as pd


@runtime_checkable
class IMarketDataProvider(ABC):
    """Interface for retrieving market data, financial statements, and pricing history."""

    @abstractmethod
    async def get_historical_prices(
        self, symbol: str, start_date: str, end_date: str, interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetch historical OHLCV price series for a given symbol asynchronously."""
        pass

    @abstractmethod
    async def get_financial_statements(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Fetch balance sheet, income statement, and cash flow statements asynchronously."""
        pass

    @abstractmethod
    async def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Fetch fundamental metadata, sector, industry, and key ratios asynchronously."""
        pass
