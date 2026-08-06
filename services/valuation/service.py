from __future__ import annotations

import logging
from typing import Any
from core.events.dispatcher import EventDispatcher
from core.events.memory_bus import InMemoryEventBus
from services.valuation.engine import ValuationEngine
from services.valuation.models import ValuationResult

logger = logging.getLogger(__name__)


class ValuationService:
    """Service orchestrating valuation calculations upon forecast completion."""

    def __init__(self, engine: ValuationEngine, event_bus: InMemoryEventBus, dispatcher: EventDispatcher) -> None:
        self._engine = engine
        self._event_bus = event_bus
        self._dispatcher = dispatcher
        self._event_bus.subscribe("forecast.completed", self.handle_forecast_completed)

    async def handle_forecast_completed(self, event: Any) -> None:
        """Handle forecast completion event and compute valuation."""
        payload = getattr(event, "payload", event)
        symbol = getattr(payload, "symbol", "RELIANCE.NS")
        if hasattr(symbol, "symbol"):
            symbol = symbol.symbol

        logger.info("ValuationService received forecast completion for symbol: %s", symbol)
        valuation_result = self._engine.compute(symbol, payload)
        
        await self._dispatcher.dispatch(
            "valuation.completed",
            {
                "symbol": symbol,
                "blended_fair_value": valuation_result.blended_fair_value,
                "margin_of_safety_pct": valuation_result.margin_of_safety_pct,
                "recommendation": valuation_result.recommendation
            }
        )
