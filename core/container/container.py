from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from core.container.registry import ServiceRegistry

T = TypeVar("T")


class Container:
    """Enterprise Dependency Injection Container for AIERP V6."""

    def __init__(self, registry: ServiceRegistry | None = None) -> None:
        self._registry = registry or ServiceRegistry()

    @property
    def registry(self) -> ServiceRegistry:
        """Access the underlying service registry."""
        return self._registry

    def register_singleton(self, interface: type[T] | str, factory: Callable[..., T]) -> None:
        """Register a singleton service factory."""
        self._registry.register_singleton(interface, factory)

    def register_transient(self, interface: type[T] | str, factory: Callable[..., T]) -> None:
        """Register a transient service factory."""
        self._registry.register_transient(interface, factory)

    def resolve(self, interface: type[T] | str) -> T:
        """Resolve an instance for the given interface or key."""
        provider = self._registry.get_provider(interface)
        if provider is None:
            raise KeyError(f"No service registered for interface/key: {interface}")
        return provider.get()
