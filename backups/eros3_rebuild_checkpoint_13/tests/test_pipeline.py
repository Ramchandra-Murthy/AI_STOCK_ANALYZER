from __future__ import annotations

import asyncio
from typing import Any

from core.events import EventDispatcher, InMemoryEventBus
from services.forecast.engine import ForecastEngine
from services.forecast.service import ForecastService
from services.fundamentals.normalizer import FinancialNormalizer
from services.fundamentals.provider import YahooFinanceProvider
from services.fundamentals.service import FundamentalsService
from services.report.engine import ReportEngine
from services.report.service import ReportService
from services.research.engine import ResearchEngine
from services.research.service import ResearchService
from services.valuation.engine import ValuationEngine
from services.valuation.service import ValuationService


def test_end_to_end_pipeline() -> None:
    """Synchronous wrapper running async end-to-end integration test with foundational Fundamentals pipeline trigger."""

    async def run_pipeline() -> None:
        bus = InMemoryEventBus()
        dispatcher = EventDispatcher(bus)

        provider = YahooFinanceProvider()
        normalizer = FinancialNormalizer()
        fundamentals_service = FundamentalsService(provider, normalizer, dispatcher)

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

        bus.subscribe("fundamentals.downloaded", spy_handler)
        bus.subscribe("forecast.completed", spy_handler)
        bus.subscribe("valuation.completed", valuation_listener)
        bus.subscribe("research.completed", research_listener)
        bus.subscribe("report.completed", report_listener)

        symbol = "RELIANCE.NS"
        await fundamentals_service.get_or_download(symbol)

        try:
            await asyncio.wait_for(pipeline_completed.wait(), timeout=2.0)
        except TimeoutError:
            raise AssertionError("Pipeline execution timed out waiting for ReportCompleted event.")

        event_names = [e.name for e in events_received]

        assert event_names.count("fundamentals.downloaded") == 1
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
