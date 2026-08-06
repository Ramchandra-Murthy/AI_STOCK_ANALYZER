from __future__ import annotations

import logging
from core.events.dispatcher import EventDispatcher
from core.events.interfaces import EventBus
from services.research.engine import ResearchEngine
from services.research.events import ResearchCompleted
from services.research.models import ResearchResult
from services.valuation.events import ValuationCompleted
from services.valuation.models import ValuationResult

logger = logging.getLogger(__name__)


class ResearchService:
    """Orchestrates research synthesis triggered by ValuationCompleted events."""

    def __init__(
        self,
        engine: ResearchEngine,
        event_bus: EventBus,
        event_dispatcher: EventDispatcher
    ) -> None:
        self._engine = engine
        self._event_bus = event_bus
        self._dispatcher = event_dispatcher

        # Subscribe to valuation completion events
        self._event_bus.subscribe("valuation.completed", self.handle_valuation_completed)

    async def handle_valuation_completed(self, event: ValuationCompleted) -> None:
        """Handler triggered when valuation analysis is completed."""
        logger.info("ResearchService received ValuationCompleted for symbol: %s", event.symbol)
        
        # Construct valuation result proxy for synthesis
        val_result = ValuationResult(
            symbol=event.symbol,
            dcf=None, # type: ignore
            relative=None, # type: ignore
            nav_value=0.0,
            blended_fair_value=event.blended_fair_value,
            current_market_price=event.blended_fair_value * (1.0 - (event.margin_of_safety_pct / 100.0)),
            margin_of_safety_pct=event.margin_of_safety_pct,
            recommendation=event.recommendation
        )

        result = self.synthesize_and_publish(val_result)
        logger.info("ResearchCompleted published for symbol: %s with Recommendation: %s", result.symbol, result.ai_recommendation)

    def synthesize_and_publish(self, valuation: ValuationResult) -> ResearchResult:
        """Synthesize research and dispatch ResearchCompleted event."""
        result = self._engine.synthesize(valuation)

        event = ResearchCompleted(
            symbol=result.symbol,
            ai_recommendation=result.ai_recommendation,
            confidence_score=result.confidence_score,
            payload={
                "symbol": result.symbol,
                "ai_recommendation": result.ai_recommendation,
                "confidence_score": result.confidence_score,
                "moat": result.economic_moat
            }
        )

        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._dispatcher.dispatch(event))
        except RuntimeError:
            asyncio.run(self._dispatcher.dispatch(event))

        return result
