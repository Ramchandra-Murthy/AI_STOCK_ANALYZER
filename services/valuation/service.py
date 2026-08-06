from __future__ import annotations

import logging
from core.events.dispatcher import EventDispatcher
from core.events.interfaces import EventBus
from services.valuation.engine import ValuationEngine
from services.valuation.events import ValuationCompleted
from services.valuation.models import ValuationResult
from services.forecast.events import ForecastCompleted

logger = logging.getLogger(__name__)


class ValuationService:
    """Orchestrates valuation execution triggered by ForecastCompleted events."""

    def __init__(
        self,
        engine: ValuationEngine,
        event_bus: EventBus,
        event_dispatcher: EventDispatcher
    ) -> None:
        self._engine = engine
        self._event_bus = event_bus
        self._dispatcher = event_dispatcher

        # Subscribe to forecast completion events
        self._event_bus.subscribe("forecast.completed", self.handle_forecast_completed)

    async def handle_forecast_completed(self, event: ForecastCompleted) -> None:
        """Handler triggered when financial forecasts are completed."""
        logger.info("ValuationService received ForecastCompleted for symbol: %s", event.symbol)
        
        result = self.compute_and_publish(event.symbol)
        logger.info("ValuationCompleted published for symbol: %s with Fair Value: %.2f", result.symbol, result.blended_fair_value)

    def compute_and_publish(self, symbol: str) -> ValuationResult:
        """Compute valuation and dispatch ValuationCompleted event."""
        result = self._engine.compute(symbol)

        event = ValuationCompleted(
            symbol=result.symbol,
            blended_fair_value=result.blended_fair_value,
            margin_of_safety_pct=result.margin_of_safety_pct,
            recommendation=result.recommendation,
            payload={
                "symbol": result.symbol,
                "blended_fair_value": result.blended_fair_value,
                "margin_of_safety_pct": result.margin_of_safety_pct,
                "recommendation": result.recommendation
            }
        )

        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._dispatcher.dispatch(event))
        except RuntimeError:
            asyncio.run(self._dispatcher.dispatch(event))

        return result
