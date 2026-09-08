from __future__ import annotations

"""Small, deterministic EROS application service container.

The restored EROS runtime uses one process-local container. Registrations are
explicit and production code never silently substitutes a fake service.
"""

from typing import Any, Callable, TypeVar

from core.container.exceptions import DuplicateServiceError, ServiceNotFoundError
from core.container.registry import ServiceKey

T = TypeVar("T")


class ServiceContainer:
    def __init__(self) -> None:
        self._singletons: dict[str, Any] = {}
        self._factories: dict[str, Callable[[], Any]] = {}

    @staticmethod
    def _key(key: str | ServiceKey) -> str:
        return str(key.value if isinstance(key, ServiceKey) else key)

    def register(self, key: str | ServiceKey, instance: Any) -> None:
        self.register_singleton(key, instance)

    def register_singleton(self, key: str | ServiceKey, instance: Any) -> None:
        normalized = self._key(key)
        if normalized in self._singletons or normalized in self._factories:
            raise DuplicateServiceError(f"Service '{normalized}' is already registered.")
        self._singletons[normalized] = instance

    def register_factory(self, key: str | ServiceKey, factory: Callable[[], Any]) -> None:
        normalized = self._key(key)
        if normalized in self._singletons or normalized in self._factories:
            raise DuplicateServiceError(f"Service '{normalized}' is already registered.")
        self._factories[normalized] = factory

    def resolve(self, key: str | ServiceKey) -> Any:
        normalized = self._key(key)
        if normalized in self._singletons:
            return self._singletons[normalized]
        if normalized in self._factories:
            return self._factories[normalized]()
        raise ServiceNotFoundError(f"Service '{normalized}' not found in container.")

    def clear(self) -> None:
        self._singletons.clear()
        self._factories.clear()


container = ServiceContainer()
