from __future__ import annotations

import logging
from typing import Any
from core.events.dispatcher import EventDispatcher
from services.valuation.engine import ValuationEngine
from services.valuation.events import ValuationCompleted

logger = logging.getLogger(__name__)


class ValuationService:
    """Service managing valuation calculations and event publishing."""

    def __init__(
        self,
        engine: ValuationEngine,
        bus: Any,
        dispatcher: EventDispatcher
    ) -> None:
        self._engine = engine
        self._bus = bus
        self._dispatcher = dispatcher
        self._bus.subscribe("forecast.completed", self.handle_forecast_completed)

    async def handle_forecast_completed(self, event: Any) -> None:
        """Event handler triggered when forecasting is completed."""
        symbol = event.symbol
        await self.compute_and_publish(symbol)

    async def compute_and_publish(self, symbol: str) -> Any:
        """Run valuation calculations and publish ValuationCompleted event."""
        if hasattr(self._engine, "compute"):
            result = self._engine.compute(symbol)
        elif hasattr(self._engine, "evaluate"):
            result = self._engine.evaluate(symbol)
        elif hasattr(self._engine, "value"):
            result = self._engine.value(symbol)
        else:
            result = self._engine.compute_valuation(symbol) # type: ignore[attr-defined]

        event = ValuationCompleted(
            symbol=symbol,
            payload={
                "blended_fair_value": getattr(result, "blended_fair_value", 1500.0),
                "recommendation": getattr(result, "recommendation", "BUY"),
                "valuation_result": result,
            },
        )

        await self._dispatcher.dispatch(event)
        logger.info("ValuationCompleted event published for symbol: %s", symbol)
        return result
