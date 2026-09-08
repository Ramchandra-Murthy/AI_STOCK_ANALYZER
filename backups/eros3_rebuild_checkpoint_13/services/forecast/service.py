from __future__ import annotations

import logging
import time
from typing import Any, Optional
from core.events.dispatcher import EventDispatcher
from services.forecast.engine import ForecastEngine
from services.forecast.events import ForecastCompleted
from services.forecast.models import ForecastResult
from services.financials.financial_statement import FinancialStatements

logger = logging.getLogger(__name__)


class ForecastService:
    """Service managing financial forecasting computations triggered by fundamental statements events."""

    def __init__(
        self,
        engine: ForecastEngine,
        bus: Any,
        dispatcher: EventDispatcher,
    ) -> None:
        self._engine = engine
        self._bus = bus
        self._dispatcher = dispatcher
        self._bus.subscribe("fundamentals.downloaded", self.handle_fundamentals_downloaded)

    async def handle_fundamentals_downloaded(self, event: Any) -> None:
        """Event handler triggered when fundamentals are successfully downloaded and normalized."""
        financials = event.payload.get("financial_statements")
        symbol = event.symbol

        if not financials:
            logger.warning("No financial statements found in payload for symbol: %s", symbol)
            return

        await self.compute_and_publish(financials)

    async def compute_and_publish(self, financials: FinancialStatements, model_type: str = "CAGR") -> ForecastResult:
        """Run forecast calculations using actual FinancialStatements and publish ForecastCompleted event."""
        symbol = financials.symbol
        result = self._engine.generate_forecast(financials, model_type=model_type)

        event = ForecastCompleted(
            symbol=symbol,
            timestamp=time.time(),
            payload={
                "forecast_result": result,
                "model_type": model_type,
                "symbol": symbol,
            },
        )

        await self._dispatcher.dispatch(event)
        logger.info("ForecastCompleted event published for symbol: %s using model: %s", symbol, model_type)
        return result
