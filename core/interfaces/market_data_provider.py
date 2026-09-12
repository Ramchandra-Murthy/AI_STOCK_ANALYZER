from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MarketDataProvider(ABC):
    @abstractmethod
    def get_market_data(self, symbol: str) -> dict[str, Any]:
        """Fetch market data for the given symbol."""
        pass
