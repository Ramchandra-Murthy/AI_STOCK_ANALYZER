from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from core.events.event import DomainEvent

E = TypeVar("E", bound=DomainEvent)
EventHandler = Callable[[E], Awaitable[None] | None]


class EventBus(ABC):
    """Abstract interface for the enterprise event bus (CORE-009)."""

    @abstractmethod
    def subscribe(self, event_name: str, handler: EventHandler[Any]) -> None:
        """Register a handler for a specific event name."""
        pass

    @abstractmethod
    def unsubscribe(self, event_name: str, handler: EventHandler[Any]) -> None:
        """Remove a handler for a specific event name."""
        pass

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Asynchronously publish a domain event to all registered handlers."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Remove all subscriptions."""
        pass

    @abstractmethod
    def subscriber_count(self, event_name: str) -> int:
        """Return the number of subscribers for a given event name."""
        pass

    @abstractmethod
    def has_subscribers(self, event_name: str) -> bool:
        """Return True if there are subscribers for the given event name."""
        pass
