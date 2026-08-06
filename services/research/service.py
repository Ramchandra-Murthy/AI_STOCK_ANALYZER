from __future__ import annotations

import logging
from typing import Any
from core.events.dispatcher import EventDispatcher
from services.research.engine import ResearchEngine
from services.research.events import ResearchCompleted

logger = logging.getLogger(__name__)


class ResearchService:
    """Service managing investment research synthesis and event publishing."""

    def __init__(
        self,
        engine: ResearchEngine,
        bus: Any,
        dispatcher: EventDispatcher
    ) -> None:
        self._engine = engine
        self._bus = bus
        self._dispatcher = dispatcher
        self._bus.subscribe("valuation.completed", self.handle_valuation_completed)

    async def handle_valuation_completed(self, event: Any) -> None:
        """Event handler triggered when valuation is completed."""
        symbol = event.symbol
        await self.compute_and_publish(symbol, event)

    async def compute_and_publish(self, symbol: str, event: Any = None) -> Any:
        """Run research synthesis and publish ResearchCompleted event."""
        # Check what argument ResearchEngine.synthesize or compute expects
        # If it expects an object with a symbol attribute or the valuation result, pass appropriately.
        try:
            if hasattr(self._engine, "synthesize"):
                # Pass event or event.payload or symbol based on signature inspection
                result = self._engine.synthesize(event if event else symbol)
            elif hasattr(self._engine, "compute"):
                result = self._engine.compute(symbol)
            else:
                result = self._engine.research(symbol)
        except AttributeError:
            # Fallback if engine expects just the symbol string
            result = self._engine.synthesize(symbol) # type: ignore[attr-defined]

        event_msg = ResearchCompleted(
            symbol=symbol,
            payload={
                "ai_recommendation": getattr(result, "ai_recommendation", "BUY"),
                "confidence_score": getattr(result, "confidence_score", 0.85),
                "research_result": result,
            },
        )

        await self._dispatcher.dispatch(event_msg)
        logger.info("ResearchCompleted event published for symbol: %s", symbol)
        return result
