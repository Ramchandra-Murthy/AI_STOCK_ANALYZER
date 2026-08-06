from __future__ import annotations

import logging
from core.events.dispatcher import EventDispatcher
from core.events.interfaces import EventBus
from services.report.engine import ReportEngine
from services.report.events import ReportCompleted
from services.report.models import GeneratedReport
from services.research.events import ResearchCompleted
from services.research.models import ResearchResult, InvestmentThesis, RiskSummary

logger = logging.getLogger(__name__)


class ReportService:
    """Orchestrates report generation triggered by ResearchCompleted events."""

    def __init__(
        self,
        engine: ReportEngine,
        event_bus: EventBus,
        event_dispatcher: EventDispatcher
    ) -> None:
        self._engine = engine
        self._event_bus = event_bus
        self._dispatcher = event_dispatcher

        # Subscribe to research completion events
        self._event_bus.subscribe("research.completed", self.handle_research_completed)

    async def handle_research_completed(self, event: ResearchCompleted) -> None:
        """Handler triggered when research analysis is completed."""
        logger.info("ReportService received ResearchCompleted for symbol: %s", event.symbol)
        
        # Construct research result proxy for report rendering
        research_result = ResearchResult(
            symbol=event.symbol,
            thesis=InvestmentThesis(summary="Synthesized automatically from event stream.", drivers=["Automated workflow"]),
            risks=RiskSummary(primary_risk="Standard market risks", mitigants=["Active monitoring"]),
            economic_moat="Wide Moat",
            ai_recommendation=event.ai_recommendation,
            confidence_score=event.confidence_score
        )

        result = self.generate_and_publish(research_result)
        logger.info("ReportCompleted published for symbol: %s with format: %s", result.symbol, result.format_type)

    def generate_and_publish(self, research: ResearchResult) -> GeneratedReport:
        """Generate reports and dispatch ReportCompleted event."""
        result = self._engine.generate(research)

        event = ReportCompleted(
            symbol=result.symbol,
            format_type=result.format_type,
            payload={
                "symbol": result.symbol,
                "format_type": result.format_type,
                "markdown_length": len(result.markdown_content),
                "html_length": len(result.html_content)
            }
        )

        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._dispatcher.dispatch(event))
        except RuntimeError:
            asyncio.run(self._dispatcher.dispatch(event))

        return result
