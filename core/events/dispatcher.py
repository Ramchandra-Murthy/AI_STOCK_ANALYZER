from __future__ import annotations

import logging
from core.events.event import DomainEvent
from core.events.interfaces import EventBus

logger = logging.getLogger(__name__)


class EventDispatcher:
    """High-level dispatcher service for publishing domain events through the EventBus."""

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    async def dispatch(self, event: DomainEvent) -> None:
        """Dispatch a domain event via the underlying event bus."""
        logger.debug("Dispatching event %s (%s)", event.name, event.event_id)
        await self._event_bus.publish(event)
