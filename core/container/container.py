"""
==========================================================
Dependency Injection Container Implementation
==========================================================
"""
from typing import Any, Callable, Dict
from core.container.exceptions import ServiceNotFoundError, DuplicateServiceError

class ServiceContainer:
    def __init__(self):
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}

    def register(self, key: str, instance: Any) -> None:
        """Alias for register_singleton for compatibility."""
        self.register_singleton(key, instance)

    def register_singleton(self, key: str, instance: Any) -> None:
        if key in self._singletons or key in self._factories:
            raise DuplicateServiceError(f"Service '{key}' is already registered.")
        self._singletons[key] = instance

    def register_factory(self, key: str, factory: Callable[[], Any]) -> None:
        if key in self._singletons or key in self._factories:
            raise DuplicateServiceError(f"Service '{key}' is already registered.")
        self._factories[key] = factory

    def resolve(self, key: str) -> Any:
        if key in self._singletons:
            return self._singletons[key]
        if key in self._factories:
            return self._factories[key]()
        raise ServiceNotFoundError(f"Service '{key}' not found in container.")

    def clear(self) -> None:
        self._singletons.clear()
        self._factories.clear()

# Global container instance
container = ServiceContainer()
