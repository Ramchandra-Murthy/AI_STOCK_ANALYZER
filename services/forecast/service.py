from __future__ import annotations

import logging
from typing import Any
from core.events.dispatcher import EventDispatcher
from services.forecast.engine import ForecastEngine
from services.forecast.events import ForecastCompleted

logger = logging.getLogger(__name__)


class ForecastService:
    """Service managing financial forecasting computations and event publishing."""

    def __init__(
        self,
        engine: ForecastEngine,
        bus: Any,
        dispatcher: EventDispatcher
    ) -> None:
        self._engine = engine
        self._bus = bus
        self._dispatcher = dispatcher
        self._bus.subscribe("market.data.downloaded", self.handle_market_data_downloaded)

    async def handle_market_data_downloaded(self, event: Any) -> None:
        """Event handler triggered when market data is downloaded."""
        market_response = event.payload.get("response")
        if not market_response:
            symbol = event.symbol
        else:
            symbol = market_response.symbol

        await self.compute_and_publish(symbol)

    async def compute_and_publish(self, symbol: str) -> Any:
        """Run forecast calculations and publish ForecastCompleted event."""
        result = self._engine.forecast(symbol)

        event = ForecastCompleted(
            symbol=symbol,
            payload={
                "forecast_result": result,
                "model_type": "DCF-GROWTH",
            },
        )

        await self._dispatcher.dispatch(event)
        logger.info("ForecastCompleted event published for symbol: %s", symbol)
        return result
