from __future__ import annotations

import asyncio
from typing import Any
from core.events import InMemoryEventBus, EventDispatcher
from services.market_data import MarketDataService, MarketDataDownloader, MarketDataCache
from services.forecast import ForecastService, ForecastEngine
from services.valuation import ValuationService, ValuationEngine
from services.research import ResearchService, ResearchEngine


def test_end_to_end_pipeline() -> None:
    """Synchronous wrapper running async end-to-end integration test through ResearchService."""
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

        research_engine = ResearchEngine()
        research_service = ResearchService(research_engine, bus, dispatcher)

        events_received: list[Any] = []

        async def spy_handler(event: Any) -> None:
            events_received.append(event)

        bus.subscribe("market.data.downloaded", spy_handler)
        bus.subscribe("forecast.completed", spy_handler)
        bus.subscribe("valuation.completed", spy_handler)
        bus.subscribe("research.completed", spy_handler)

        symbol = "RELIANCE.NS"
        await market_service.get_or_download(symbol)

        # Allow async event loop ticks for the full event cascade to process
        await asyncio.sleep(0.2)

        event_names = [e.name for e in events_received]
        assert "market.data.downloaded" in event_names
        assert "forecast.completed" in event_names
        assert "valuation.completed" in event_names
        assert "research.completed" in event_names

        # Verify research outcome
        valuation_result = valuation_engine.compute(symbol)
        research_result = research_engine.synthesize(valuation_result)
        assert research_result.symbol == symbol
        assert research_result.ai_recommendation in ["BUY", "HOLD", "SELL"]
        assert research_result.confidence_score > 0.0

    asyncio.run(run_pipeline())
