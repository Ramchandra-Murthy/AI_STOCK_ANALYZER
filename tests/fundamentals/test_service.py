from __future__ import annotations

import asyncio
import pytest
from core.events.bus import InMemoryEventBus
from core.events.dispatcher import EventDispatcher
from services.fundamentals.normalizer import FinancialNormalizer
from services.fundamentals.provider import YahooFinanceProvider
from services.fundamentals.service import FundamentalsService


def test_fundamentals_service_get_or_download_and_cache() -> None:
    async def run() -> None:
        bus = InMemoryEventBus()
        dispatcher = EventDispatcher(bus)
        provider = YahooFinanceProvider()
        normalizer = FinancialNormalizer()
        service = FundamentalsService(provider, normalizer, dispatcher)

        events_received = []
        async def listener(event: Any) -> None:
            events_received.append(event)

        bus.subscribe("fundamentals.downloaded", listener)

        symbol = "RELIANCE.NS"
        fs1 = await service.get_or_download(symbol)
        assert fs1.symbol == symbol
        assert len(events_received) == 1

        # Second call should hit cache
        fs2 = await service.get_or_download(symbol)
        assert fs2 == fs1
        assert len(events_received) == 2

    asyncio.run(run())
