from __future__ import annotations

import abc
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from backend.exceptions import ServiceError

logger = logging.getLogger(__name__)

class ProviderError(ServiceError):
    """Base exception for external market data provider failures."""
    pass

class RateLimitError(ProviderError):
    """Raised when an external provider rate limit is exceeded."""
    pass

class ProviderResponse(abc.ABC):
    symbol: str
    provider_name: str
    timestamp: datetime
    raw_data: Dict[str, Any]

class BaseDataProvider(abc.ABC):
    """Abstract base class for all institutional market data providers."""

    def __init__(self, provider_name: str, api_key: Optional[str] = None) -> None:
        self.provider_name = provider_name
        self.api_key = api_key
        self.logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def fetch_historical_prices(self, symbol: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fetch historical OHLCV price series."""
        pass

    @abc.abstractmethod
    def fetch_financial_statements(self, symbol: str) -> Dict[str, Any]:
        """Fetch income statement, balance sheet, and cash flow statements."""
        pass

    @abc.abstractmethod
    def check_health(self) -> bool:
        """Verify provider availability and connectivity."""
        pass