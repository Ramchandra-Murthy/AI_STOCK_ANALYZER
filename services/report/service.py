from __future__ import annotations

import logging
from typing import Any
from core.events.dispatcher import EventDispatcher
from services.report.engine import ReportEngine
from services.report.events import ReportCompleted

logger = logging.getLogger(__name__)


class ReportService:
    """Service managing multi-format report generation and event publishing."""

    def __init__(
        self,
        engine: ReportEngine,
        bus: Any,
        dispatcher: EventDispatcher
    ) -> None:
        self._engine = engine
        self._bus = bus
        self._dispatcher = dispatcher
        self._bus.subscribe("research.completed", self.handle_research_completed)

    async def handle_research_completed(self, event: Any) -> None:
        """Event handler triggered when research is completed."""
        symbol = event.symbol
        await self.compute_and_publish(symbol, event)

    async def compute_and_publish(self, symbol: str, event: Any = None) -> Any:
        """Run report generation and publish ReportCompleted event."""
        if hasattr(self._engine, "generate"):
            try:
                result = self._engine.generate(event if event else symbol)
            except TypeError:
                result = self._engine.generate(symbol)
        elif hasattr(self._engine, "compute"):
            result = self._engine.compute(symbol)
        else:
            result = self._engine.build_report(symbol) # type: ignore[attr-defined]

        event_msg = ReportCompleted(
            symbol=symbol,
            payload={
                "format_type": "MULTI-FORMAT",
                "report_result": result,
            },
        )

        await self._dispatcher.dispatch(event_msg)
        logger.info("ReportCompleted event published for symbol: %s", symbol)
        return result
