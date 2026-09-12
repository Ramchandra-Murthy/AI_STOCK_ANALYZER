from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MarketEvent:
    event_id: str
    event_type: str  # e.g. "PRICE_TICK", "EARNINGS_RELEASE", "MACRO_UPDATE"
    symbol: str
    payload: dict[str, Any]
    priority: int = 1  # 1 = High, 5 = Low
    source: str = "ExchangeFeed"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class RealTimeEventDispatcher:
    """Real-time event dispatcher routing incoming market events to downstream analytical engines."""

    def __init__(self) -> None:
        self._event_log: list[MarketEvent] = []

    def dispatch(self, event: MarketEvent) -> dict[str, Any]:
        logger.info(
            "Dispatching real-time event %s of type %s for %s",
            event.event_id,
            event.event_type,
            event.symbol,
        )
        self._event_log.append(event)

        # Determine automated action based on event type
        action_triggered = "NO_ACTION"
        if event.event_type == "PRICE_TICK":
            action_triggered = "REFRESH_VALUATION_CHECK"
        elif event.event_type == "EARNINGS_RELEASE":
            action_triggered = "TRIGGER_FULL_RESEARCH_PIPELINE"
        elif event.event_type == "MACRO_UPDATE":
            action_triggered = "REFRESH_PORTFOLIO_RISK_BUDGET"

        return {
            "event_id": event.event_id,
            "status": "PROCESSED",
            "action_triggered": action_triggered,
            "timestamp": event.timestamp,
        }
