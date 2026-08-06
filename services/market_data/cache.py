from __future__ import annotations

import logging
from typing import Optional
from services.market_data.models import MarketDataResponse

logger = logging.getLogger(__name__)


class MarketDataCache:
    """In-memory or persistent cache for market data responses."""

    def __init__(self) -> None:
        self._store: dict[str, MarketDataResponse] = {}

    def get(self, symbol: str) -> Optional[MarketDataResponse]:
        """Retrieve cached market data for a symbol if available."""
        data = self._store.get(symbol.upper())
        if data:
            logger.debug("Cache hit for symbol: %s", symbol)
        return data

    def set(self, symbol: str, data: MarketDataResponse) -> None:
        """Cache market data for a symbol."""
        self._store[symbol.upper()] = data
        logger.debug("Cached market data for symbol: %s (%d records)", symbol, len(data.records))

    def clear(self) -> None:
        """Clear all cached data."""
        self._store.clear()
