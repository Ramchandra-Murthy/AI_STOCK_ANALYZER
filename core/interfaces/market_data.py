from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd


class IMarketDataProvider(ABC):
    """Interface for retrieving market data, financial statements, and pricing history."""

    @abstractmethod
    def get_historical_prices(
        self, symbol: str, start_date: str, end_date: str, interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetch historical OHLCV price series for a given symbol."""
        pass

    @abstractmethod
    def get_financial_statements(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Fetch balance sheet, income statement, and cash flow statements."""
        pass

    @abstractmethod
    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Fetch fundamental metadata, sector, industry, and key ratios."""
        pass
