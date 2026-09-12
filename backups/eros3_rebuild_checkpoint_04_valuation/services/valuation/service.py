from __future__ import annotations

import logging
import time
from typing import Any

from core.events.dispatcher import EventDispatcher
from services.forecast.models import ForecastResult
from services.valuation.dcf.engine import ProductionDCFEngine
from services.valuation.events import ValuationCompleted

logger = logging.getLogger(__name__)


class ValuationService:
    """Service managing production-grade DCF valuation and event publishing triggered by forecast completion."""

    def __init__(
        self,
        engine: Any,
        bus: Any,
        dispatcher: EventDispatcher,
    ) -> None:
        self._engine = engine
        self._dcf_engine = ProductionDCFEngine()
        self._bus = bus
        self._dispatcher = dispatcher
        self._bus.subscribe("forecast.completed", self.handle_forecast_completed)

    async def handle_forecast_completed(self, event: Any) -> None:
        """Event handler triggered when forecasting is completed."""
        forecast_result: ForecastResult = event.payload.get("forecast_result")
        symbol = event.symbol

        if not forecast_result:
            logger.warning("No forecast result found in payload for symbol: %s", symbol)
            return

        await self.compute_and_publish(forecast_result)

    async def compute_and_publish(self, forecast: ForecastResult) -> Any:
        """Run production DCF valuation and publish ValuationCompleted event."""
        symbol = forecast.symbol
        dcf_result = self._dcf_engine.calculate(forecast)

        # Determine recommendation based on fair value vs benchmark (e.g., current price mock ~1400)
        fair_value = dcf_result.fair_value_per_share
        recommendation = "BUY" if fair_value > 1200 else ("HOLD" if fair_value > 900 else "SELL")

        event = ValuationCompleted(
            symbol=symbol,
            timestamp=time.time(),
            payload={
                "blended_fair_value": fair_value,
                "recommendation": recommendation,
                "dcf_result": dcf_result,
                "valuation_result": dcf_result,
                "symbol": symbol,
            },
        )

        await self._dispatcher.dispatch(event)
        logger.info(
            "ValuationCompleted event published for symbol: %s with fair value: %.2f",
            symbol,
            fair_value,
        )
        return dcf_result
