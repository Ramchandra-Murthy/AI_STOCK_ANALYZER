from __future__ import annotations

from typing import Any, Callable, Dict, Type, TypeVar
from core.container.providers import BaseProvider, SingletonProvider, TransientProvider

T = TypeVar("T")


class ServiceRegistry:
    """Registry responsible for mapping interface contracts to container providers."""

    def __init__(self) -> None:
        self._providers: Dict[Type[Any] | str, BaseProvider[Any]] = {}

    def register_singleton(self, interface: Type[T] | str, factory: Callable[..., T]) -> None:
        """Register a singleton service binding."""
        self._providers[interface] = SingletonProvider(factory)

    def register_transient(self, interface: Type[T] | str, factory: Callable[..., T]) -> None:
        """Register a transient service binding."""
        self._providers[interface] = TransientProvider(factory)

    def get_provider(self, interface: Type[T] | str) -> BaseProvider[T] | None:
        """Retrieve the provider bound to the given interface or key."""
        return self._providers.get(interface)

    def has(self, interface: Type[T] | str) -> bool:
        """Check if a service is registered."""
        return interface in self._providers
