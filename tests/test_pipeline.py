from __future__ import annotations

import asyncio
from typing import Any
from core.events import InMemoryEventBus, EventDispatcher
from services.market_data import MarketDataService, MarketDataDownloader, MarketDataCache
from services.forecast import ForecastService, ForecastEngine
from services.valuation import ValuationService, ValuationEngine
from services.research import ResearchService, ResearchEngine


def test_end_to_end_pipeline() -> None:
    """Synchronous wrapper running async end-to-end integration test asserting strictly on event payloads."""
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
        valuation_events: list[Any] = []
        research_events: list[Any] = []

        async def spy_handler(event: Any) -> None:
            events_received.append(event)

        async def valuation_listener(event: Any) -> None:
            valuation_events.append(event)

        async def research_listener(event: Any) -> None:
            research_events.append(event)

        bus.subscribe("market.data.downloaded", spy_handler)
        bus.subscribe("forecast.completed", spy_handler)
        bus.subscribe("valuation.completed", valuation_listener)
        bus.subscribe("research.completed", research_listener)

        symbol = "RELIANCE.NS"
        await market_service.get_or_download(symbol)

        # Allow async event loop ticks for the full event cascade to process
        await asyncio.sleep(0.2)

        event_names = [e.name for e in events_received]
        assert "market.data.downloaded" in event_names
        assert "forecast.completed" in event_names

        # Assert directly on event outputs rather than manual engine invocation
        assert len(valuation_events) == 1
        assert valuation_events[0].symbol == symbol
        assert valuation_events[0].blended_fair_value > 0.0
        assert valuation_events[0].recommendation in {"BUY", "HOLD", "SELL"}

        assert len(research_events) == 1
        assert research_events[0].symbol == symbol
        assert research_events[0].ai_recommendation in {"BUY", "HOLD", "SELL"}
        assert research_events[0].confidence_score > 0.0

    asyncio.run(run_pipeline())
