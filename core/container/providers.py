from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar, Generic

T = TypeVar("T")


class BaseProvider(ABC, Generic[T]):
    """Abstract base provider for container resolutions."""

    @abstractmethod
    def get(self) -> T:
        """Resolve and return an instance of the target service."""
        pass


class SingletonProvider(BaseProvider[T]):
    """Provider that maintains a single shared instance across resolutions."""

    def __init__(self, factory: Callable[..., T]) -> None:
        self._factory = factory
        self._instance: T | None = None

    def get(self) -> T:
        if self._instance is None:
            self._instance = self._factory()
        return self._instance


class TransientProvider(BaseProvider[T]):
    """Provider that instantiates a new instance on every resolution request."""

    def __init__(self, factory: Callable[..., T]) -> None:
        self._factory = factory

    def get(self) -> T:
        return self._factory()
