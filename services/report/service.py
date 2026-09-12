from __future__ import annotations

import logging
import time
from typing import Any

from core.events.dispatcher import EventDispatcher
from services.report.events import ReportCompleted

logger = logging.getLogger(__name__)


class ReportService:
    """Service managing multi-format professional reporting triggered by analysis completion."""

    def __init__(
        self,
        engine: Any,
        bus: Any,
        dispatcher: EventDispatcher,
    ) -> None:
        self._engine = engine
        self._bus = bus
        self._dispatcher = dispatcher
        self._bus.subscribe("research.completed", self.handle_research_completed)

    async def handle_research_completed(self, event: Any) -> None:
        """Event handler triggered when research analysis is completed."""
        symbol = event.symbol
        payload = event.payload or {}
        await self.generate_and_publish(symbol, payload)

    async def generate_and_publish(self, symbol: str, analysis_data: dict[str, Any]) -> Any:
        """Generate professional report and publish ReportCompleted event."""
        result = self._engine.generate(
            symbol, format_type="MULTI-FORMAT", analysis_data=analysis_data
        )

        event = ReportCompleted(
            symbol=symbol,
            timestamp=time.time(),
            payload={
                "format_type": result.format_type,
                "file_path": result.file_path,
                "report_result": result,
                "symbol": symbol,
            },
        )

        await self._dispatcher.dispatch(event)
        logger.info(
            "ReportCompleted event published for symbol: %s at %s", symbol, result.file_path
        )
        return result
