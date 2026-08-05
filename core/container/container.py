from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class ServiceContainer:
    """Enterprise-grade lightweight service container for DI."""

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}
        self._factories: dict[str, Callable[[ServiceContainer], Any]] = {}

    def register_instance(self, key: str, instance: Any) -> None:
        """Register a pre-instantiated singleton service."""
        self._services[key] = instance

    def register_factory(self, key: str, factory: Callable[[ServiceContainer], Any]) -> None:
        """Register a lazy factory function for service instantiation."""
        self._factories[key] = factory

    def resolve(self, key: str) -> Any:
        """Resolve a service by its key, invoking its factory if necessary."""
        if key in self._services:
            return self._services[key]

        if key in self._factories:
            instance = self._factories[key](self)
            self._services[key] = instance
            return instance

        raise KeyError(f"Service key '{key}' is not registered in the container.")


# Global container instance
container = ServiceContainer()
