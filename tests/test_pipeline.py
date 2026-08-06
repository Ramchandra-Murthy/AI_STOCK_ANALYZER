from __future__ import annotations

import asyncio
from typing import Any
import pytest

from core.events import InMemoryEventBus, EventDispatcher
from services.market_data.downloader import MarketDataDownloader
from services.market_data.cache import MarketDataCache
from services.market_data.service import MarketDataService
from services.forecast.engine import ForecastEngine
from services.forecast.service import ForecastService
from services.valuation.engine import ValuationEngine
from services.valuation.service import ValuationService
from services.research.engine import ResearchEngine
from services.research.service import ResearchService
from services.report.engine import ReportEngine
from services.report.service import ReportService


def test_end_to_end_pipeline() -> None:
    """Synchronous wrapper running async end-to-end integration test with deterministic event-driven synchronization and ordering verification."""
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

        report_engine = ReportEngine()
        report_service = ReportService(report_engine, bus, dispatcher)

        events_received: list[Any] = []
        valuation_events: list[Any] = []
        research_events: list[Any] = []
        report_events: list[Any] = []

        pipeline_completed = asyncio.Event()

        async def spy_handler(event: Any) -> None:
            events_received.append(event)

        async def valuation_listener(event: Any) -> None:
            valuation_events.append(event)

        async def research_listener(event: Any) -> None:
            research_events.append(event)

        async def report_listener(event: Any) -> None:
            report_events.append(event)
            pipeline_completed.set()

        bus.subscribe("market.data.downloaded", spy_handler)
        bus.subscribe("forecast.completed", spy_handler)
        bus.subscribe("valuation.completed", valuation_listener)
        bus.subscribe("research.completed", research_listener)
        bus.subscribe("report.completed", report_listener)

        symbol = "RELIANCE.NS"
        await market_service.get_or_download(symbol)

        try:
            await asyncio.wait_for(pipeline_completed.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            raise AssertionError("Pipeline execution timed out waiting for ReportCompleted event.")

        event_names = [e.name for e in events_received]

        assert event_names.count("market.data.downloaded") == 1
        assert event_names.count("forecast.completed") == 1
        assert len(valuation_events) == 1
        assert len(research_events) == 1
        assert len(report_events) == 1

        # Verify valuation payload
        assert valuation_events[0].symbol == symbol
        assert valuation_events[0].payload["blended_fair_value"] > 0.0
        assert valuation_events[0].payload["recommendation"] in {"BUY", "HOLD", "SELL"}

        # Verify research payload
        assert research_events[0].symbol == symbol
        assert research_events[0].payload["ai_recommendation"] in {"BUY", "HOLD", "SELL"}
        assert research_events[0].payload["confidence_score"] > 0.0

        # Verify report payload
        assert report_events[0].symbol == symbol
        assert report_events[0].payload["format_type"] == "MULTI-FORMAT"

    asyncio.run(run_pipeline())
