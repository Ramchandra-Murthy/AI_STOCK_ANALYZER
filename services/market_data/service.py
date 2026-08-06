from __future__ import annotations

import logging
from core.events.dispatcher import EventDispatcher
from services.market_data.cache import MarketDataCache
from services.market_data.downloader import MarketDataDownloader
from services.market_data.events import MarketDataDownloaded
from services.market_data.models import MarketDataResponse

logger = logging.getLogger(__name__)


class MarketDataService:
    """Orchestrates market data downloading, caching, and event publication."""

    def __init__(
        self,
        downloader: MarketDataDownloader,
        cache: MarketDataCache,
        event_dispatcher: EventDispatcher
    ) -> None:
        self._downloader = downloader
        self._cache = cache
        self._dispatcher = event_dispatcher

    async def get_or_download(self, symbol: str) -> MarketDataResponse:
        """Retrieve market data from cache or download, then publish MarketDataDownloaded event."""
        cached = self._cache.get(symbol)
        if cached:
            response = cached
            source = "Cache"
        else:
            response = await self._downloader.fetch(symbol)
            self._cache.set(symbol, response)
            source = response.source

        # Publish domain event
        event = MarketDataDownloaded(
            symbol=response.symbol,
            records=len(response.records),
            source=source,
            payload={
                "symbol": response.symbol,
                "records": len(response.records),
                "source": source
            }
        )
        await self._dispatcher.dispatch(event)
        return response
