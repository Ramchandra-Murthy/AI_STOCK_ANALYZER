from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from core.events.event import DomainEvent
from core.events.interfaces import EventBus, EventHandler

logger = logging.getLogger(__name__)


class InMemoryEventBus(EventBus):
    """Enterprise in-memory event bus supporting sync and async event handlers."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler[Any]]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler[Any]) -> None:
        """Register a handler for a specific event name."""
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)
            logger.debug("Subscribed handler %s to event '%s'", handler, event_name)

    def unsubscribe(self, event_name: str, handler: EventHandler[Any]) -> None:
        """Remove a handler for a specific event name."""
        if event_name in self._subscribers and handler in self._subscribers[event_name]:
            self._subscribers[event_name].remove(handler)
            logger.debug("Unsubscribed handler %s from event '%s'", handler, event_name)

    async def publish(self, event: DomainEvent) -> None:
        """Asynchronously publish a domain event to all registered handlers."""
        handlers = self._subscribers.get(event.name, [])
        if not handlers:
            logger.debug("No subscribers found for event '%s'", event.name)
            return

        logger.debug(
            "Publishing event '%s' (%s) to %d handlers", event.name, event.event_id, len(handlers)
        )

        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.exception(
                    "Error handling event '%s' with handler %s: %s", event.name, handler, e
                )

    def clear(self) -> None:
        """Remove all subscriptions."""
        self._subscribers.clear()
        logger.debug("Cleared all event bus subscriptions.")

    def subscriber_count(self, event_name: str) -> int:
        """Return the number of subscribers for a given event name."""
        return len(self._subscribers.get(event_name, []))

    def has_subscribers(self, event_name: str) -> bool:
        """Return True if there are subscribers for the given event name."""
        return self.subscriber_count(event_name) > 0
