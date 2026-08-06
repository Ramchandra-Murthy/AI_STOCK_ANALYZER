from __future__ import annotations

import logging
from core.events.dispatcher import EventDispatcher
from core.events.interfaces import EventBus
from services.forecast.engine import ForecastEngine
from services.forecast.events import ForecastCompleted
from services.forecast.models import ForecastResult
from services.market_data.events import MarketDataDownloaded
from services.market_data.models import MarketDataResponse

logger = logging.getLogger(__name__)


class ForecastService:
    """Orchestrates forecast generation triggered by MarketDataDownloaded events."""

    def __init__(
        self,
        engine: ForecastEngine,
        event_bus: EventBus,
        event_dispatcher: EventDispatcher
    ) -> None:
        self._engine = engine
        self._event_bus = event_bus
        self._dispatcher = event_dispatcher
        
        # Subscribe to market data events
        self._event_bus.subscribe("market.data.downloaded", self.handle_market_data_downloaded)

    async def handle_market_data_downloaded(self, event: MarketDataDownloaded) -> None:
        """Handler triggered when market data is downloaded."""
        logger.info("ForecastService received MarketDataDownloaded for symbol: %s", event.symbol)
        
        # In a fully integrated runtime, we fetch or receive the MarketDataResponse.
        # For pipeline orchestration, we construct a corresponding payload response or query cache.
        from services.market_data.downloader import MarketDataDownloader
        downloader = MarketDataDownloader()
        market_response = await downloader.fetch(event.symbol)
        
        result = self.compute_and_publish(market_response)
        logger.info("ForecastCompleted published for symbol: %s", result.symbol)

    def compute_and_publish(self, market_data: MarketDataResponse) -> ForecastResult:
        """Compute forecast and dispatch ForecastCompleted event synchronously/asynchronously."""
        result = self._engine.compute(market_data)
        
        event = ForecastCompleted(
            symbol=result.symbol,
            model_type=result.model_type,
            payload={
                "symbol": result.symbol,
                "model_type": result.model_type,
                "revenue_cagr": result.revenue.cagr,
                "eps_cagr": result.eps.cagr
            }
        )
        # Dispatch event asynchronously via event loop if running
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._dispatcher.dispatch(event))
        except RuntimeError:
            asyncio.run(self._dispatcher.dispatch(event))
            
        return result
