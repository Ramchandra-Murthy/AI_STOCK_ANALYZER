from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from core.container.providers import BaseProvider, SingletonProvider, TransientProvider

T = TypeVar("T")


class ServiceRegistry:
    """Registry responsible for mapping interface contracts to container providers."""

    def __init__(self) -> None:
        self._providers: dict[type[Any] | str, BaseProvider[Any]] = {}

    def register_singleton(self, interface: type[T] | str, factory: Callable[..., T]) -> None:
        """Register a singleton service binding."""
        self._providers[interface] = SingletonProvider(factory)

    def register_transient(self, interface: type[T] | str, factory: Callable[..., T]) -> None:
        """Register a transient service binding."""
        self._providers[interface] = TransientProvider(factory)

    def get_provider(self, interface: type[T] | str) -> BaseProvider[T] | None:
        """Retrieve the provider bound to the given interface or key."""
        return self._providers.get(interface)

    def has(self, interface: type[T] | str) -> bool:
        """Check if a service is registered."""
        return interface in self._providers
