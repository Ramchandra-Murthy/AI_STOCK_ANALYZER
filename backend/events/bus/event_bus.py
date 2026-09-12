from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class EnterpriseEventBus:
    """Centralized publish-subscribe event bus for routing normalized market events to subscribers."""

    _subscribers: dict[str, list[Callable[[dict[str, Any]], None]]] = {}

    @classmethod
    def subscribe(cls, event_type: str, callback: Callable[[dict[str, Any]], None]) -> None:
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        cls._subscribers[event_type].append(callback)
        logger.info("Subscriber registered for event type: %s", event_type)

    @classmethod
    def publish(cls, event_type: str, payload: dict[str, Any]) -> int:
        callbacks = cls._subscribers.get(event_type, [])
        logger.info("Publishing event '%s' to %s subscribers", event_type, len(callbacks))
        for callback in callbacks:
            try:
                callback(payload)
            except Exception as e:
                logger.error("Error dispatching event to subscriber: %s", e)
        return len(callbacks)

    @classmethod
    def clear(cls) -> None:
        cls._subscribers.clear()
