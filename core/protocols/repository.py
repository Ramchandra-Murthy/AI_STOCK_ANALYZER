from __future__ import annotations

from typing import Any, Protocol, runtime_checkable, TypeVar

T = TypeVar("T")

@runtime_checkable
class RepositoryProtocol(Protocol[T]):
    """Generic repository protocol for domain aggregates."""
    def get_by_id(self, identifier: Any) -> T | None:
        ...

    def save(self, aggregate: T) -> None:
        ...

