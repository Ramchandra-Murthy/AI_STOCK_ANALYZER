from __future__ import annotations
from typing import Any, Callable

class ServiceContainer:
    def __init__(self) -> None:
        self._services: dict[str, Any] = {}
        self._factories: dict[str, Callable[[], Any]] = {}

    def register(self, name: str, service: Any) -> None:
        if name in self._services or name in self._factories:
            raise ValueError(f"Service \x27{name}\x27 already registered.")
        self._services[name] = service

    def register_instance(self, name: str, service: Any) -> None:
        self.register(name, service)

    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        if name in self._services or name in self._factories:
            raise ValueError(f"Service \x27{name}\x27 already registered.")
        self._factories[name] = factory

    def resolve(self, name: str) -> Any:
        if name in self._services:
            return self._services[name]
        if name in self._factories:
            # Optionally cache factory-created singletons or return fresh instances
            service = self._factories[name]()
            self._services[name] = service
            return service
        raise KeyError(f"Service \x27{name}\x27 not registered.")

    def clear(self) -> None:
        self._services.clear()
        self._factories.clear()

container = ServiceContainer()
