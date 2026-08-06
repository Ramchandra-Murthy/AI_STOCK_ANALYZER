from __future__ import annotations

import asyncio
from core.events import InMemoryEventBus, EventDispatcher
from services.market_data import MarketDataService, MarketDataDownloader, MarketDataCache
from services.forecast import ForecastService, ForecastEngine
from services.valuation import ValuationService, ValuationEngine


def test_end_to_end_pipeline() -> None:
    """Synchronous wrapper running async end-to-end integration test for MarketData -> Forecast -> Valuation."""
    async def run_pipeline() -> None:
        bus = InMemoryEventBus()
        dispatcher = EventDispatcher(bus)

        downloader = MarketDataDownloader()
        cache = MarketDataCache()
        market_service = MarketDataService(downloader, cache, dispatcher)

        forecast_engine = ForecastEngine()
        forecast_service = ForecastService(forecast_engine, bus, dispatcher)

        valuation_engine = ValuationEngine()
        valuation_service = ValuationService(valuation_engine, bus, dispatcher)

        events_received: list[Any] = []

        async def spy_handler(event: Any) -> None:
            events_received.append(event)

        bus.subscribe("market.data.downloaded", spy_handler)
        bus.subscribe("forecast.completed", spy_handler)
        bus.subscribe("valuation.completed", spy_handler)

        symbol = "RELIANCE.NS"
        response = await market_service.get_or_download(symbol)

        # Allow async event loop ticks for handlers to process
        await asyncio.sleep(0.1)

        event_names = [e.name for e in events_received]
        assert "market.data.downloaded" in event_names
        assert "forecast.completed" in event_names
        assert "valuation.completed" in event_names

        # Verify valuation outcomes
        valuation_result = valuation_engine.compute(symbol)
        assert valuation_result.symbol == symbol
        assert valuation_result.blended_fair_value > 0.0
        assert valuation_result.recommendation in ["BUY", "HOLD", "SELL"]

    asyncio.run(run_pipeline())
